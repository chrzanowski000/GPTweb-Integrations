import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from backend.lmstudio import extract_formula
from backend.sheets import append_formula_rows, _get_or_create_spreadsheet, _get_client
from backend.validators import validate_formula

load_dotenv()

LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")

app = FastAPI(title="Formula Archiver Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Message(BaseModel):
    role: str
    content: str


class ArchiveRequest(BaseModel):
    chat_title: str
    source: str = ""
    messages: list[Message]


def _check_lmstudio() -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{LMSTUDIO_BASE_URL}/v1/models")
            return r.status_code == 200
    except Exception:
        return False


def _check_google_sheets() -> bool:
    try:
        _get_or_create_spreadsheet(_get_client())
        return True
    except Exception:
        return False


@app.get("/health")
def health() -> dict:
    return {
        "backend": True,
        "lmstudio": _check_lmstudio(),
        "google_sheets": _check_google_sheets(),
    }


@app.post("/archive")
def archive(request: ArchiveRequest) -> dict:
    logging.info("archive request source=%s", request.source)
    # Build conversation text
    lines = [
        f"{msg.role.capitalize()}: {msg.content}" for msg in request.messages
    ]
    conversation_text = "\n\n".join(lines)

    # Extract via LM Studio
    try:
        raw = extract_formula(conversation_text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio unavailable: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Formula extraction failed: {exc}") from exc

    # Validate
    try:
        formula = validate_formula(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Formula validation failed: {exc}") from exc

    # Write to Google Sheets
    ingredients = [
        {"ingredient": ing.ingredient, "pct": ing.pct, "concentration": ing.concentration}
        for ing in formula.ingredients
    ]
    try:
        rows_written = append_formula_rows(
            formula.formula_name,
            formula.version,
            ingredients,
            description=formula.description,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Google Sheets write failed: {exc}") from exc

    return {
        "status": "ok",
        "formula_name": formula.formula_name,
        "version": formula.version,
        "rows_written": rows_written,
    }
