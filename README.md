# 📚 eLearning Slack Bot

Jeden Morgen um 09:00 Uhr bekommt jeder Mitarbeiter automatisch 3 Lernfragen per Slack DM.

```
GitHub Actions  →  sendet täglich Fragen (kostenlos)
Railway         →  empfängt Button-Klicks (kostenlos)
Google Sheets   →  speichert alle Daten
```

---

## Ordnerstruktur

```
elearning-bot/
├── bot/
│   ├── send_daily.py   ← wird von GitHub Actions gestartet
│   ├── webhook.py      ← läuft dauerhaft auf Railway
│   ├── sheets.py       ← Google Sheets Logik (geteilt)
│   └── messages.py     ← Slack Nachrichten bauen (geteilt)
├── .github/
│   └── workflows/
│       └── daily_send.yml  ← Zeitplan für GitHub Actions
├── requirements.txt
├── Procfile            ← sagt Railway wie der Server startet
└── README.md
```

---

## Einrichtung (einmalig, ca. 30 Minuten)

### 1 — GitHub Repository erstellen

1. Geh auf [github.com](https://github.com) → **New repository**
2. Name: `elearning-bot` → **Create repository**
3. Alle Dateien aus diesem Ordner hochladen
   (grüner Button **"uploading an existing file"**)

---

### 2 — Slack App erstellen

1. Geh auf [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch**
3. Name: `eLearning Bot` → Workspace wählen → **Create App**

**Berechtigungen** (OAuth & Permissions → Bot Token Scopes):
- `chat:write` — Nachrichten senden
- `im:write` — Direktnachrichten senden

4. **Install to Workspace** → erlauben
5. **Bot User OAuth Token** (`xoxb-...`) kopieren → brauchst du in Schritt 4

**Signing Secret** (Basic Information → Signing Secret) → ebenfalls kopieren

---

### 3 — Google Sheets Zugang einrichten

1. Geh auf [console.cloud.google.com](https://console.cloud.google.com)
2. Neues Projekt erstellen (z.B. `elearning-bot`)
3. APIs aktivieren: **Google Sheets API** + **Google Drive API**
4. **Service Account** erstellen:
   - IAM & Admin → Service Accounts → **+ Create**
   - Name: `elearning-bot` → Rolle: `Editor` → **Done**
   - Auf den Service Account klicken → **Keys** → **Add Key** → **JSON** → herunterladen
5. Den Inhalt der JSON-Datei komplett kopieren (brauchst du in Schritt 4)
6. Die E-Mail aus der JSON (`client_email`) in Google Drive zur Datei
   `elearning_google_drive` als **Editor** einladen

---

### 4 — Geheimnisse in GitHub hinterlegen

Dein Token kommt **nie** in den Code — nur als Secret in GitHub.

1. GitHub → dein Repository → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** → zwei Secrets anlegen:

| Name | Wert |
|---|---|
| `SLACK_BOT_TOKEN` | `xoxb-dein-token-hier` |
| `GOOGLE_CREDENTIALS_JSON` | kompletter Inhalt der JSON-Datei |

---

### 5 — Mitarbeiter eintragen

In `bot/send_daily.py` die Liste befüllen:

```python
MITARBEITER = [
    {"slack_id": "U012AB3CD", "ma_id": "MA-001", "name": "Anna Becker"},
    {"slack_id": "U056EF7GH", "ma_id": "MA-002", "name": "Tom Fischer"},
]
```

**Slack User ID herausfinden:**
In Slack → auf Namen klicken → **Profil anzeigen** → **...** → **Member-ID kopieren**

Änderung in GitHub speichern (committen) → fertig.

---

### 6 — Railway einrichten (für Button-Klicks)

1. Geh auf [railway.app](https://railway.app) → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo** → `elearning-bot` auswählen
3. Warten bis Deploy fertig ist (ca. 2 Minuten)
4. **Settings** → **Domains** → **Generate Domain** → URL kopieren
   (sieht aus wie `https://elearning-bot-production.up.railway.app`)
5. Unter **Variables** dieselben zwei Variablen eintragen:
   - `SLACK_BOT_TOKEN` = dein Token
   - `GOOGLE_CREDENTIALS_JSON` = komplette JSON

---

### 7 — Railway URL in Slack eintragen

1. [api.slack.com/apps](https://api.slack.com/apps) → deine App → **Interactivity & Shortcuts**
2. **On** einschalten
3. Request URL: `https://DEINE-URL.up.railway.app/slack/interaktiv`
4. **Save Changes**

---

## Testen

**Manuell auslösen** (ohne auf 09:00 Uhr warten):
- GitHub → dein Repository → **Actions** → **eLearning Täglicher Versand** → **Run workflow**

**Prüfen ob alles funktioniert:**
- Du bekommst eine Slack DM mit 3 Fragen
- Du klickst eine Antwort → Feedback erscheint als Thread
- Im Google Sheet **📊 Mitarbeiter-Tracking** erscheint ein neuer Eintrag

---

## Täglicher Ablauf (automatisch)

```
Mo–Fr 09:00 Uhr
  GitHub Actions startet send_daily.py
  → lädt Fragen aus Google Sheets
  → wählt 3 Fragen pro Mitarbeiter (adaptiv)
  → sendet Slack DM an jeden Mitarbeiter

Mitarbeiter klickt Antwort-Button
  → Slack schickt Klick an Railway (webhook.py)
  → Feedback erscheint sofort als Thread
  → Ergebnis wird in Google Sheets gespeichert
```

---

## Neue Fragen hinzufügen

Rovo-Fragen hier in den Chat einfügen → aktualisierte Excel-Datei
herunterladen → in Google Drive ersetzen → Bot nimmt sie automatisch
am nächsten Tag auf. Fertig!
