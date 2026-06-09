# Servicio B - API de Monitoreo

Microservicio FastAPI encargado de registrar URLs, consultar PostgreSQL, verificar disponibilidad de sitios web y actualizar el estado de cada servidor.

## Tecnologias

- Python 3.11
- FastAPI
- Uvicorn
- psycopg2-binary
- requests

## Variables de entorno

| Variable | Valor por defecto |
| --- | --- |
| `DB_HOST` | `servicio-c` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `server_monitor` |
| `DB_USER` | `admin` |
| `DB_PASSWORD` | `admin123` |
| `PORT` | `8000` |

## Endpoints

### `POST /monitor`

Registra una URL para monitoreo.

```json
{
  "url": "https://google.com"
}
```

Respuesta:

```json
{
  "message": "URL registrada correctamente"
}
```

### `GET /servers`

Lista todos los servidores registrados en PostgreSQL.

### `POST /check`

Ejecuta el monitoreo de todas las URLs registradas. Cada sitio se consulta con timeout de 5 segundos y se actualizan `estado`, `tiempoRespuesta` y `ultimoCheck`.

Respuesta:

```json
{
  "checked": 5,
  "success": true
}
```

### `GET /health`

Verifica el estado del microservicio.

```json
{
  "service": "Servicio B",
  "status": "OK"
}
```

## Construir imagen Docker

```bash
docker build -t servicio-b-monitor .
```

## Ejecutar contenedor

```bash
docker run -p 8000:8000 servicio-b-monitor
```

Si el Servicio A del proyecto apunta a `servicio-b:4000`, ejecutar el contenedor con `PORT=4000` o ajustar el proxy/compose para usar el puerto `8000`.

```bash
docker run -e PORT=4000 -p 4000:4000 servicio-b-monitor
```
