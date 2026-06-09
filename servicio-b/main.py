from datetime import datetime
from time import perf_counter
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from database import (
    get_all_servers,
    initialize_database,
    insert_server_url,
    update_server_status,
)


app = FastAPI(
    title="Servicio B - Monitor de Servidores",
    description="API de monitoreo y procesamiento para URLs registradas.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MonitorRequest(BaseModel):
    url: HttpUrl


def serialize_server(server: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte fechas de PostgreSQL a JSON compatible."""
    serialized = dict(server)
    for field in ("ultimoCheck", "fechaRegistro"):
        value = serialized.get(field)
        if isinstance(value, datetime):
            serialized[field] = value.isoformat()
    return serialized


def check_url(url: str) -> Dict[str, Optional[int] | str]:
    start_time = perf_counter()
    try:
        requests.get(url, timeout=5)
        elapsed_ms = int((perf_counter() - start_time) * 1000)
        return {"estado": "UP", "tiempoRespuesta": elapsed_ms}
    except requests.RequestException:
        elapsed_ms = int((perf_counter() - start_time) * 1000)
        return {"estado": "DOWN", "tiempoRespuesta": elapsed_ms}


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.post("/monitor")
def register_url(payload: MonitorRequest) -> Dict[str, str]:
    url = str(payload.url)
    try:
        created = insert_server_url(url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error al registrar la URL") from exc

    if not created:
        return {"message": "URL ya registrada"}

    return {"message": "URL registrada correctamente"}


@app.get("/servers")
def list_servers() -> List[Dict[str, Any]]:
    try:
        servers = get_all_servers()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error al listar servidores") from exc

    return jsonable_encoder([serialize_server(server) for server in servers])


@app.post("/check")
def run_monitoring() -> Dict[str, Any]:
    try:
        servers = get_all_servers()
        for server in servers:
            result = check_url(server["url"])
            update_server_status(
                server["url"],
                str(result["estado"]),
                int(result["tiempoRespuesta"]) if result["tiempoRespuesta"] is not None else None,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error al ejecutar monitoreo") from exc

    return {"checked": len(servers), "success": True}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"service": "Servicio B", "status": "OK"}
