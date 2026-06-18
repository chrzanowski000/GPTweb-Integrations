import os
import re
from datetime import datetime, timezone

import gspread
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "GPTweb-integration-test")
INDEX_SHEET_NAME = "Index"
INDEX_HEADER = ["Timestamp", "Formula Name", "Version", "Description", "Sheet Name"]
FORMULA_HEADER = ["Ingredient", "Percent"]

_client: gspread.Client | None = None


def _load_oauth_credentials() -> Credentials:
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    client_secret_path = os.getenv("GOOGLE_CLIENT_SECRET_PATH", "client_secret.json")

    creds: Credentials | None = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as fh:
            fh.write(creds.to_json())

    return creds


def _get_client() -> gspread.Client:
    global _client
    if _client is None:
        creds = _load_oauth_credentials()
        _client = gspread.authorize(creds)
    return _client


def _get_or_create_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    id_file = os.getenv("SHEET_ID_PATH", "sheet_id.txt")

    if os.path.exists(id_file):
        spreadsheet_id = open(id_file).read().strip()
        return client.open_by_key(spreadsheet_id)

    spreadsheet = client.create(SPREADSHEET_NAME)
    with open(id_file, "w") as fh:
        fh.write(spreadsheet.id)

    print(f"Created spreadsheet '{SPREADSHEET_NAME}' (id: {spreadsheet.id})")
    return spreadsheet


def _get_or_create_index(spreadsheet: gspread.Spreadsheet) -> gspread.Worksheet:
    """Return the Index worksheet, creating it with a header row if needed."""
    try:
        return spreadsheet.worksheet(INDEX_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        # Rename the default blank Sheet1 if it exists, otherwise add a new one.
        try:
            ws = spreadsheet.sheet1
            ws.update_title(INDEX_SHEET_NAME)
        except Exception:
            ws = spreadsheet.add_worksheet(title=INDEX_SHEET_NAME, rows=1000, cols=5)
        ws.append_row(INDEX_HEADER, value_input_option="USER_ENTERED")
        return ws


def _safe_sheet_name(formula_name: str, version: str) -> str:
    """Build a worksheet name that is safe for Google Sheets (max 100 chars, no special chars)."""
    name = f"{formula_name} v{version}"
    name = re.sub(r"[\\/*?\[\]:]", "", name)
    return name[:100]


def _unique_sheet_name(spreadsheet: gspread.Spreadsheet, base_name: str) -> str:
    """Return base_name if unused, otherwise base_name (2), (3), etc."""
    existing = {ws.title for ws in spreadsheet.worksheets()}
    if base_name not in existing:
        return base_name
    counter = 2
    while f"{base_name} ({counter})" in existing:
        counter += 1
    return f"{base_name} ({counter})"


def _create_formula_worksheet(
    spreadsheet: gspread.Spreadsheet,
    sheet_name: str,
    ingredients: list[dict],
) -> str:
    """Create a new worksheet for this formula and populate it. Returns the final sheet name."""
    sheet_name = _unique_sheet_name(spreadsheet, sheet_name)
    ws = spreadsheet.add_worksheet(title=sheet_name, rows=len(ingredients) + 2, cols=2)
    rows = [FORMULA_HEADER] + [[item["ingredient"], item["pct"]] for item in ingredients]
    ws.update(rows, "A1")
    ws.format("A1:B1", {"textFormat": {"bold": True}})
    return sheet_name


def append_formula_rows(
    formula_name: str,
    version: str,
    ingredients: list[dict],
    description: str = "",
) -> int:
    """Write a new formula worksheet and update the Index.

    Returns the number of ingredient rows written.
    """
    client = _get_client()
    spreadsheet = _get_or_create_spreadsheet(client)
    index_ws = _get_or_create_index(spreadsheet)

    sheet_name = _safe_sheet_name(formula_name, version)
    _create_formula_worksheet(spreadsheet, sheet_name, ingredients)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    index_ws.append_row(
        [timestamp, formula_name, version, description, sheet_name],
        value_input_option="USER_ENTERED",
    )

    return len(ingredients)


if __name__ == "__main__":
    rows_written = append_formula_rows(
        formula_name="Test Formula",
        version="1",
        description="A simple woody test formula.",
        ingredients=[
            {"ingredient": "Iso E Super", "pct": 50},
            {"ingredient": "Hedione", "pct": 30},
        ],
    )
    print(f"Wrote {rows_written} ingredient row(s) successfully.")
