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
FORMULA_HEADER = ["Ingredient", "Concentration [%]", "Solution Weight [g]", "Pure Material [%]", "Relative %"]
TARGET_WEIGHT_G = 5.0

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
    target_weight_g: float = TARGET_WEIGHT_G,
) -> str:
    """Create a new worksheet for this formula and populate it. Returns the final sheet name."""
    sheet_name = _unique_sheet_name(spreadsheet, sheet_name)

    total_pct = sum(item["pct"] for item in ingredients) or 1.0

    data_rows = []
    sum_solution_g = 0.0
    sum_pure_g = 0.0

    for item in ingredients:
        pct = item["pct"]
        conc = item.get("concentration", 10.0) or 10.0
        pure_g = round(pct / 100 * target_weight_g, 4)
        solution_g = round(pure_g / (conc / 100), 4)
        relative_pct = round(pct / total_pct * 100, 2)
        sum_solution_g += solution_g
        sum_pure_g += pure_g
        data_rows.append([item["ingredient"], conc, solution_g, pct, relative_pct])

    alcohol_g = round(target_weight_g - sum_solution_g, 4)
    formula_conc_pct = round(sum_pure_g / target_weight_g * 100, 2)

    summary_rows = [
        [],
        ["Alcohol [g]", "", round(alcohol_g, 4), "", ""],
        ["Total Solution [g]", "", round(sum_solution_g, 4), "", ""],
        ["Total Pure Material [g]", "", "", round(sum_pure_g, 4), ""],
        ["Target Weight [g]", "", target_weight_g, "", ""],
        ["Formula Concentration [%]", "", "", formula_conc_pct, ""],
    ]

    all_rows = [FORMULA_HEADER] + data_rows + summary_rows
    total_rows = len(all_rows) + 2

    ws = spreadsheet.add_worksheet(title=sheet_name, rows=total_rows, cols=5)
    ws.update(all_rows, "A1")

    # Bold header row
    ws.format("A1:E1", {"textFormat": {"bold": True}})
    # Bold summary labels in column A
    summary_start = len(data_rows) + 3  # header + data + blank row + 1-based
    summary_end = summary_start + len(summary_rows) - 2  # exclude the blank
    ws.format(
        f"A{summary_start}:A{summary_end}",
        {"textFormat": {"bold": True}},
    )

    return sheet_name


def append_formula_rows(
    formula_name: str,
    version: str,
    ingredients: list[dict],
    description: str = "",
    target_weight_g: float = TARGET_WEIGHT_G,
) -> int:
    """Write a new formula worksheet and update the Index.

    Returns the number of ingredient rows written.
    """
    client = _get_client()
    spreadsheet = _get_or_create_spreadsheet(client)
    index_ws = _get_or_create_index(spreadsheet)

    sheet_name = _safe_sheet_name(formula_name, version)
    _create_formula_worksheet(spreadsheet, sheet_name, ingredients, target_weight_g=target_weight_g)

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
            {"ingredient": "Iso E Super", "pct": 50, "concentration": 10},
            {"ingredient": "Hedione", "pct": 30, "concentration": 10},
        ],
    )
    print(f"Wrote {rows_written} ingredient row(s) successfully.")
