# GPTweb-Integrations — Formula Archiver

Save fragrance formulas from any source — ChatGPT, browser, notes, or typed directly — to Google Sheets via a local LM Studio model. Everything runs locally: no cloud AI, no external databases.

---

## Overview

Four ways to archive a formula:

```
1. Firefox auto-detect:   ChatGPT tab → type #SAVE_FORMULA → extension captures + sends
2. Firefox manual paste:  Extension popup → paste recipe → Archive Formula button
3. Android share:         Any app → Share → Formula Archiver (needs #SAVE_FORMULA in text)
4. Android manual:        Formula Archiver app → Archive tab → paste recipe → Archive Formula
```

All four paths hit the same backend:

```
Client → POST /archive → FastAPI backend → LM Studio (local LLM) → Google Sheets
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | For the backend |
| Firefox | For the extension |
| [LM Studio](https://lmstudio.ai/) | Running locally at `http://127.0.0.1:1234` with a model loaded |
| Google Cloud project | Sheets API + Drive API enabled, OAuth 2.0 Desktop App client |
| Android Studio | Only needed to build/install the Android app |
| Tailscale | Only needed for Android on a real device over a different network |

---

## Backend Setup

### Install dependencies

```bash
git clone <repo-url>
cd GPTweb-Integrations
python -m venv .venv
source .venv/bin/activate      # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

### Google Cloud / OAuth setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) → select your project
2. **APIs & Services → Library** → enable **Google Sheets API** and **Google Drive API**
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
4. Choose **Desktop App**, give it a name, click Create
5. Download the JSON and save it as `client_secret.json` in the project root
6. On first backend start a browser window opens for OAuth consent — approve it. `token.json` is saved automatically.

### .env configuration

Edit `.env` (copied from `.env.example`):

```env
GOOGLE_CLIENT_SECRET_PATH=client_secret.json
GOOGLE_TOKEN_PATH=token.json
SHEET_ID_PATH=sheet_id.txt
SPREADSHEET_NAME=GPTweb-integration-test
LMSTUDIO_BASE_URL=http://127.0.0.1:1234
```

All paths are relative to the project root. Only `SPREADSHEET_NAME` and `LMSTUDIO_BASE_URL` normally need changing.

### Running the backend

**Standard (Firefox extension only):**
```bash
source .venv/bin/activate
uvicorn backend.app:app --reload
```

**Required for Android (emulator or real device):**
```bash
source .venv/bin/activate
uvicorn backend.app:app --reload --host 0.0.0.0
```

The `--host 0.0.0.0` flag makes the server accept connections from outside localhost. Without it, the Android app cannot reach the backend.

### WSL2 + Tailscale (real Android device only)

If you run the backend inside WSL2 and use Tailscale to connect a real phone, the backend is not directly visible to Tailscale (which runs on Windows, not inside WSL2). Add a Windows port proxy to bridge them.

Open **PowerShell as Administrator** on Windows:

```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=127.0.0.1
```

Verify it was added:
```powershell
netsh interface portproxy show all
```

To remove it later:
```powershell
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

After adding the proxy, the phone can reach the backend at the machine's Tailscale IP (e.g., `http://100.x.x.x:8000`).

### Health check

Open `http://localhost:8000/health` (or the Tailscale IP from the phone). Expected response:

```json
{"backend": true, "lmstudio": true, "google_sheets": true}
```

All three should be `true` before using any client.

---

## Firefox Extension

### Loading

1. Open `about:debugging` in Firefox
2. Click **This Firefox** → **Load Temporary Add-on**
3. Select `extension/manifest.json`
4. The Formula Archiver icon appears in the toolbar

> The extension is temporary — it must be reloaded after each Firefox restart. To reload without restarting: go back to `about:debugging` and click **Reload** next to Formula Archiver.

### Auto-detect mode

Automatically watches a ChatGPT tab for the trigger phrase.

1. Open [chatgpt.com](https://chatgpt.com) and **reload the tab** if it was open before you loaded the extension
2. Click the extension icon → **Monitor This Tab** (button turns red "Stop Monitoring")
3. Chat about a fragrance formula with GPT
4. Send `#SAVE_FORMULA` as your message
5. A green toast notification confirms the formula was saved; red shows any error

The extension captures the **last assistant message** before the trigger and sends it to the backend.

### Manual paste mode

Archive any formula text without ChatGPT or the trigger phrase.

1. Click the extension icon
2. Paste the recipe text into the **"Paste recipe here…"** textarea under the divider
3. Click **Archive Formula**
4. The result appears below the button: green = saved (formula name + version), red = error
5. Click **Clear** to reset the textarea and result

No trigger phrase is required. The text is sent directly to the backend.

---

## Android App

### Build and install

1. Open Android Studio → **File → Open** → select the `android/` folder inside this project
2. Wait for Gradle sync to complete (first sync downloads dependencies — may take a few minutes)
3. Connect your phone via USB, or start an emulator: **Device Manager → Play**
4. Click the green **Run** button (▶) or press **Shift+F10**
5. The app installs and opens automatically

### Settings tab

Tap the **Settings** tab (bottom navigation bar) to configure:

| Field | Emulator value | Real device value |
|---|---|---|
| Backend URL | `http://10.0.2.2:8000` | `http://<tailscale-ip>:8000` |
| Trigger Phrase | `#SAVE_FORMULA` | `#SAVE_FORMULA` |

- `10.0.2.2` is the Android emulator's fixed alias for the host machine's loopback interface
- For a real device, use the Tailscale IP of your desktop (see WSL2 + Tailscale section above)

Tap **Test Connection** to verify the backend is reachable before using the share or archive features. It calls `GET /health` and shows "Backend Connected" or an error message for 3 seconds.

Tap **Save Settings** to persist changes.

### Manual Archive tab (no trigger phrase)

The app opens on the **Archive** tab by default.

1. Paste any recipe text into the text field
2. Tap **Archive Formula**
3. Spinner appears while the backend processes
4. Success card shows: formula name, version, rows written
5. Tap **Clear** to reset the field and result, or **Dismiss** on the result card

No trigger phrase check. Text is sent directly to the backend.

### Share mode (from any app)

Used when you have a formula in ChatGPT, a browser, or a notes app and want to save it via the share menu. **The shared text must contain the trigger phrase** (default `#SAVE_FORMULA`).

1. In any app, select the text or use the app's share/export button
2. Tap **Share** → **Formula Archiver** from the share sheet
   - If Formula Archiver is not visible, scroll right on the share sheet or tap **More apps**
3. The app opens, processes the text, and shows the result
4. Tap **Dismiss** to close

**ChatGPT mobile workaround:** ChatGPT's text-selection menu replaces the standard Android share option. Instead:
1. Copy the formula text from ChatGPT
2. Open Samsung Notes (or any notes app) and paste it
3. Add `#SAVE_FORMULA` at the end
4. Select all text → **Share** → **Formula Archiver**

Alternatively, share the whole ChatGPT conversation page: tap **⋮ (three dots)** in ChatGPT → **Share** → **Formula Archiver**.

---

## Formula Formats

The LLM understands two input styles. Both work from any client.

### Percentage-based

Ingredients are listed with their percentage of the total formula. Concentrations (stock dilutions) may be stated or inferred.

```
Woody Amber v2

Iso E Super 40%
Hedione 25%
Linalool 15%
Bergamot 20%

#SAVE_FORMULA
```

The LLM reads percentages directly as `pct`. If no dilution is mentioned and percentages sum to ~100%, the concentration defaults to 100 (neat/undiluted).

### Weight-based (gram-based)

Ingredients are listed with a solution weight in grams and a stock concentration. This is the format ChatGPT often generates when you ask for a recipe by weight.

```
Fragrance Portion (1.0 g)
Material         Stock Strength   Weight (g)
Cypriol          10%              0.300
Patchouli        10%              0.250
Cade             1%               0.800
```

The LLM computes `pct` for each ingredient as:

```
pure_i       = weight_i × (concentration_i / 100)
total_pure   = sum of all pure_i
pct_i        = pure_i / target_weight_g × 100
```

The target weight is extracted from the formula header (e.g., `"Fragrance Portion (1.0 g)"` → `target_weight_g = 1.0`). If not stated, it defaults to 5 g.

This means the spreadsheet solution weights will exactly match the original recipe at the stated batch size.

---

## Sheet Format

Each saved formula creates a new worksheet tab named `<Formula Name> v<version>`.

| Column | Description |
|---|---|
| Ingredient | Name of the material |
| Concentration [%] | Stock solution strength (100 = neat, 10 = 10% dilution, 1 = 1%, etc.) |
| Solution Weight [g] | Grams of stock solution to weigh at the target batch size |
| Pure Material [%] | Pure material as % of target weight |
| Relative % | Each ingredient's share of total pure material (always sums to 100%) |

Summary rows at the bottom:

| Row | Description |
|---|---|
| Alcohol [g] | Solvent needed (can be negative if total solution exceeds target — expected for very dilute stocks) |
| Total Solution [g] | Sum of all stock solution weights |
| Total Pure Material [g] | Sum of all pure material weights |
| Target Weight [g] | Batch size (extracted from formula or default 5 g) |
| Formula Concentration [%] | Total pure material as % of target weight |

An **Index** tab is updated automatically with: timestamp, formula name, version, description, worksheet name.

---

## Troubleshooting

### Backend

| Symptom | Fix |
|---|---|
| `/health` shows `lmstudio: false` | Start LM Studio and load a model; check it is running at port 1234 |
| `/health` shows `google_sheets: false` | Delete `token.json` and restart the backend to re-authenticate |
| `token.json` expired | Delete `token.json`; the backend re-authenticates on the next request |
| Backend port already in use | Another process on port 8000; change with `--port 8001` |

### Firefox extension

| Symptom | Fix |
|---|---|
| Extension fires on old `#SAVE_FORMULA` in history | Reload the ChatGPT tab after loading the extension |
| No toast notification appears | Reload the ChatGPT tab; check the `about:debugging` console for errors |
| Manual paste shows no response | Check the browser console in `about:debugging`; verify backend URL in `background.js` (`BACKEND_URL`) |

### Android app

| Symptom | Fix |
|---|---|
| "Cannot Reach Backend" in Settings | Start backend with `--host 0.0.0.0`; confirm the URL in Settings is correct |
| "Cannot Reach Backend" on real device | Add the Windows Tailscale port proxy (see WSL2 + Tailscale section above) |
| "Keyword Not Found" on share | Add `#SAVE_FORMULA` to the shared text, or use the Manual Archive tab instead |
| Formula Archiver not in share sheet | Scroll right on the share sheet, or tap **More apps** |
| Share option missing in ChatGPT mobile | Use the notes app workaround (see Share mode section above) |

### Spreadsheet

| Symptom | Fix |
|---|---|
| Alcohol shows as negative | Expected when stocks are heavily diluted — total solution weight > target weight |
| LLM extracts wrong percentages | Reformat the formula more clearly, e.g. `Ingredient 40%` on separate lines |
| Duplicate formula name | The sheet appends `(2)`, `(3)` etc. automatically — no action needed |

---

## Files That Must Stay Gitignored

| File | Reason |
|---|---|
| `client_secret.json` | OAuth client secret — never commit |
| `token.json` | OAuth refresh token — never commit |
| `sheet_id.txt` | Auto-generated spreadsheet ID — safe to delete and recreate |
| `.env` | Contains local paths and configuration |
