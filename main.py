"""
main.py — A small notes app: FastAPI web server, notes stored in PostgreSQL.
The database connection comes from environment variables set in compose.yaml.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, StringConstraints

STATIC = Path(__file__).parent / "static"


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        row_factory=dict_row,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS notes (
                   id SERIAL PRIMARY KEY,
                   text TEXT NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL DEFAULT now()
               )"""
        )
    yield


app = FastAPI(title="Notes", lifespan=lifespan)


class NewNote(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/notes")
def list_notes():
    with connect() as conn:
        return conn.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC").fetchall()


@app.post("/api/notes", status_code=201)
def add_note(note: NewNote):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO notes (text) VALUES (%s) RETURNING id, text, created_at", (note.text,)
        ).fetchone()


@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    with connect() as conn:
        if conn.execute("DELETE FROM notes WHERE id = %s", (note_id,)).rowcount == 0:
            raise HTTPException(404, "Note not found")
