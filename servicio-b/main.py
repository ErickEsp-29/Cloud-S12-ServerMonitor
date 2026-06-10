from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests as http_requests
import time
from psycopg2.extras import RealDictCursor
from database import get_connection, close_connection

app = FastAPI(title="Servicio B - Monitor de URLs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str


@app.get("/health")
def health():
    return {"service": "Servicio B", "status": "OK"}


@app.get("/api/estado")
def listar_servidores():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM servidores ORDER BY id")
        rows = cursor.fetchall()
        resultado = []
        for row in rows:
            r = dict(row)
            if r.get("ultimocheck"):
                r["ultimoCheck"] = r.pop("ultimocheck").isoformat()
            if r.get("tiemporespuesta") is not None:
                r["tiempoRespuesta"] = r.pop("tiemporespuesta")
            resultado.append(r)
        cursor.close()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.post("/api/agregar")
def agregar_url(data: URLInput):
    if not data.url.startswith("http"):
        return {"ok": False, "error": "URL inválida. Debe comenzar con http:// o https://"}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM servidores WHERE url = %s", (data.url,))
        if cursor.fetchone():
            cursor.close()
            return {"ok": False, "error": "Esta URL ya está registrada"}

        cursor.execute("INSERT INTO servidores (url) VALUES (%s)", (data.url,))
        conn.commit()
        cursor.close()

        # Primer chequeo inmediato
        try:
            inicio = time.time()
            http_requests.get(data.url, timeout=5)
            tiempo_ms = int((time.time() - inicio) * 1000)
            estado = "up"
        except Exception:
            tiempo_ms = 0
            estado = "down"

        cursor2 = conn.cursor()
        cursor2.execute(
            "UPDATE servidores SET estado = %s, tiemporespuesta = %s, ultimocheck = NOW() WHERE url = %s",
            (estado, tiempo_ms, data.url)
        )
        conn.commit()
        cursor2.close()
        return {"ok": True, "message": "Servidor agregado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.delete("/api/eliminar")
def eliminar_url(data: URLInput):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM servidores WHERE url = %s", (data.url,))
        conn.commit()
        cursor.close()
        return {"ok": True, "message": "Servidor eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.post("/check")
def ejecutar_chequeo():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT url FROM servidores")
        servidores = cursor.fetchall()
        cursor.close()

        for servidor in servidores:
            url = servidor["url"]
            try:
                inicio = time.time()
                http_requests.get(url, timeout=5)
                tiempo_ms = int((time.time() - inicio) * 1000)
                estado = "up"
            except Exception:
                tiempo_ms = 0
                estado = "down"

            c = conn.cursor()
            c.execute(
                "UPDATE servidores SET estado = %s, tiemporespuesta = %s, ultimocheck = NOW() WHERE url = %s",
                (estado, tiempo_ms, url)
            )
            c.close()

        conn.commit()
        return {"checked": len(servidores), "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()