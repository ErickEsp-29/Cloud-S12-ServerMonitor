import os
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "servicio-c"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "server_monitor"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
}


def get_connection():
    """Crea una conexion nueva a PostgreSQL usando variables de entorno."""
    return psycopg2.connect(**DB_CONFIG)


def close_connection(conn, cursor=None):
    """Cierra el cursor y la conexión de forma segura."""
    if cursor:
        cursor.close()
    if conn:
        conn.close()


@contextmanager
def database_cursor(commit: bool = False) -> Generator[RealDictCursor, None, None]:
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        close_connection(connection)


def initialize_database() -> None:
    """Asegura que la tabla requerida exista con las columnas esperadas."""
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS servidores (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                estado VARCHAR(20) DEFAULT 'PENDING',
                tiempoRespuesta INTEGER,
                ultimoCheck TIMESTAMP,
                fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            ALTER TABLE servidores
            ADD COLUMN IF NOT EXISTS fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )


def insert_server_url(url: str) -> bool:
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO servidores (url, estado, fechaRegistro)
            VALUES (%s, %s, NOW())
            ON CONFLICT (url) DO NOTHING
            """,
            (url, "PENDING"),
        )
        return cursor.rowcount > 0


def get_all_servers() -> List[Dict]:
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, url, estado, tiempoRespuesta, ultimoCheck, fechaRegistro
            FROM servidores
            ORDER BY id ASC
            """
        )
        return list(cursor.fetchall())


def update_server_status(url: str, estado: str, tiempo_respuesta: Optional[int]) -> None:
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE servidores
            SET estado = %s,
                tiempoRespuesta = %s,
                ultimoCheck = NOW()
            WHERE url = %s
            """,
            (estado, tiempo_respuesta, url),
        )
