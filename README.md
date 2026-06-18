# GPTweb-Integrations — ChatGPT Formula Archiver

Monitors ChatGPT tabs in Firefox, detects the `#SAVE_FORMULA` trigger, extracts fragrance formulas via a local LM Studio model, and writes them to Google Sheets. Everything runs locally — no cloud AI, no external databases.

---

## How It Works

```
ChatGPT tab → Firefox Extension → FastAPI backend → LM Studio (local) → Google Sheets
```

1. Activate monitoring on a ChatGPT tab via the extension popup
2. Chat about a fragrance formula, then send `#SAVE_FORMULA` as a message
3. The extension captures the last GPT message and sends it to the backend
4. The backend sends it to LM Studio for formula extraction and validates with Pydantic
5. The formula is written to a new worksheet in Google Sheets and the Index tab is updated

---

## Prerequisites

- Python 3.11+
- Firefox
- [LM Studio](https://lmstudio.ai/) running locally at `http://127.0.0.1:1234` with a model loaded
- A Google Cloud project with **Google Sheets API** and **Google Drive API** enabled, plus an OAuth 2.0 Desktop App client

---

## Installation

```bash
git clone <repo-url>
cd GPTweb-Integrations
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

---

## Google Cloud Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select your project
2. Go to **APIs & Services → Library** and enable:
   - Google Sheets API
   - Google Drive API
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
4. Choose **Desktop App**, give it a name, and click Create
5. Download the JSON file and save it as `client_secret.json` in the project root
6. On first backend start, a browser window will open for OAuth consent — approve it. `token.json` is saved automatically for future runs.

---

## Running the Backend

```bash
source .venv/bin/activate
uvicorn backend.app:app --reload
```

Check it is healthy: open `http://localhost:8000/health` — it should return:

```json
{"backend": true, "lmstudio": true, "google_sheets": true}
```

The first time Google Sheets is contacted, a browser opens for OAuth consent.

---

## Loading the Firefox Extension

1. Open `about:debugging` in Firefox
2. Click **This Firefox** → **Load Temporary Add-on**
3. Select `extension/manifest.json`
4. The Formula Archiver icon appears in the toolbar

> The extension is temporary — it must be reloaded after each Firefox restart.

---

## Using It

1. Open [ChatGPT](https://chatgpt.com) and **reload the tab** if it was already open before you loaded the extension
2. Click the extension icon → **Monitor This Tab**
3. Chat about a fragrance formula with GPT
4. Send `#SAVE_FORMULA` as your message
5. A green notification confirms the formula was saved; a red one shows any error

---

## Sheet Format

Each saved formula gets its own worksheet tab:

| Ingredient | Concentration [%] | Solution Weight [g] | Pure Material [%] | Relative % |
|---|---|---|---|---|
| Iso E Super | 10 | 1.0 | 20.0 | 25.0 |
| ... | | | | |

Weights are calculated for a **5 g total target weight**. Summary rows at the bottom show:

- Alcohol needed (g)
- Total solution weight (g)
- Total pure material (g)
- Target weight (5 g)
- Formula concentration (%)

An **Index** tab is updated automatically with timestamp, formula name, version, description, and worksheet name.

### Concentration Rules (applied automatically by LM Studio)

| Situation | Concentration used |
|---|---|
| Formula percentages sum to ~100% | 100% (neat/undiluted) |
| Conversation explicitly mentions a dilution (e.g. "10% solution") | That value per ingredient |
| Not stated | 10% default |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/health` shows `lmstudio: false` | Start LM Studio and load a model |
| `/health` shows `google_sheets: false` | Delete `token.json` and restart the backend to re-authenticate |
| Extension fires on old `#SAVE_FORMULA` in history | Reload the ChatGPT tab after loading the extension |
| No toast notification appears | Reload the ChatGPT tab; check the `about:debugging` console for errors |
| Backend not reachable | Ensure `uvicorn` is running and listening on port 8000 |
| `token.json` expired | Delete `token.json`; the backend re-authenticates on the next request |

---

## Files That Must Stay Gitignored

| File | Reason |
|---|---|
| `client_secret.json` | OAuth client secret — never commit |
| `token.json` | OAuth refresh token — never commit |
| `sheet_id.txt` | Auto-generated spreadsheet ID — safe to delete and recreate |
