# Android App — Testing Guide

## Prerequisites

- Android Studio installed with an emulator running (Pixel 8, API 35)
- Backend running: `uvicorn backend.app:app --reload --host 0.0.0.0`
- App installed on emulator via Android Studio Run

## Settings

Open the app from the launcher and configure:

| Field | Value for emulator |
|---|---|
| Backend URL | `http://10.0.2.2:8000` |
| Trigger Phrase | `#SAVE_FORMULA` |

> `10.0.2.2` is the emulator's fixed alias for the host machine's loopback.
> The backend must start with `--host 0.0.0.0` to accept connections from the emulator.

Tap **Test Connection** to verify before testing the share flow.

---

## Sending Test Intents via ADB

Use `adb shell am start` to simulate a share from any app without needing a real device.

### Escaping rules (adb only — not relevant in real usage)

| Character | Problem | Fix |
|---|---|---|
| `#` | Android shell treats it as a comment and strips it | Wrap the entire value in `"..."` |
| `%xx` | adb URL-decodes percent-encoded sequences | Escape as `\%` |

These issues only affect adb testing. When text is shared from a real Android app, it arrives as-is with no escaping needed.

### Template

```bash
adb shell am start \
  -n com.formulaarchiver/.ShareReceiverActivity \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT '"YOUR TEXT HERE"'
```

Always:
- Use `-n` flag for the component name
- Wrap the text value in `'"...'` (outer single quotes for local shell, inner double quotes for Android shell)
- Escape `%` as `\%`

---

## Test Cases

### Test 1 — No trigger (should be blocked)

```bash
adb shell am start \
  -n com.formulaarchiver/.ShareReceiverActivity \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT '"Hello world"'
```

Expected: **Keyword Not Found** card. No network request sent.

---

### Test 2 — Trigger only

```bash
adb shell am start \
  -n com.formulaarchiver/.ShareReceiverActivity \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT '"#SAVE_FORMULA"'
```

Expected: request sent to backend. Result depends on backend/LM Studio response.

---

### Test 3 — Short formula with trigger

```bash
adb shell am start \
  -n com.formulaarchiver/.ShareReceiverActivity \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT '"Amber X7 Iso E Super 35\% Hedione 20\% #SAVE_FORMULA"'
```

Expected: spinner → **Formula Archived** card with formula name, version, rows written.

---

### Test 4 — Full formula with percentages and newlines

```bash
adb shell am start \
  -n com.formulaarchiver/.ShareReceiverActivity \
  -a android.intent.action.SEND \
  -t text/plain \
  --es android.intent.extra.TEXT '"Amber X7\n\nIso E Super 35\%\nHedione 20\%\nAmbroxan 15\%\nCedarwood 10\%\nMusk Ambrette 8\%\nVetiver 5\%\nBergamot 4\%\nPatchouli 3\%\n\n#SAVE_FORMULA"'
```

Expected: spinner → **Formula Archived** card.

---

## Checking Logs

In Android Studio open the **Logcat** tab and filter by:

```
com.formulaarchiver
```

OkHttp logs the full request and response body — useful for debugging what was sent to the backend and what came back.

---

## Real Device Testing

1. Enable **Developer Options** on the phone: Settings → About Phone → tap **Build Number** 7 times
2. Enable **USB Debugging** in Developer Options
3. Connect via USB — Android Studio detects it automatically as a target
4. On the real device, use the actual Android **Share** menu from any app (ChatGPT, browser, notes)
5. Select **Formula Archiver** from the share sheet
6. Backend URL must be the Tailscale address or LAN IP of your desktop, e.g. `http://192.168.1.x:8000`
