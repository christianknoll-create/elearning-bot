"""
send_daily.py
─────────────
Wird von GitHub Actions täglich um 09:00 Uhr gestartet.
Sendet 3 Fragen per Slack DM an jeden Mitarbeiter.

Umgebungsvariablen (in GitHub → Settings → Secrets):
  SLACK_BOT_TOKEN        → xoxb-...
  GOOGLE_CREDENTIALS_JSON → { ... komplett JSON ... }
"""

import os, time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sheets import get_alle_fragen, waehle_fragen
from messages import baue_frage_block

# ── Konfiguration ────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
FRAGEN_PRO_TAG  = 3

# ── Mitarbeiterliste ─────────────────────────────────────────────
# Slack User ID: In Slack → Profil anzeigen → (...) → Member-ID kopieren
MITARBEITER = [
    {"slack_id": "U061EJVA4LX", "ma_id": "MA-001", "name": "Marion"},
    {"slack_id": "U061XJCHV9A", "ma_id": "MA-002", "name": "Maren"},
    {"slack_id": "U07342Y9H6K", "ma_id": "MA-003", "name": "Marvin"},
    {"slack_id": "U08UZ6K3PU6", "ma_id": "MA-004", "name": "Vithu"},
    {"slack_id": "U0A8Y841QKV", "ma_id": "MA-005", "name": "Meena"},
    {"slack_id": "U0A4Q2D1KNC", "ma_id": "MA-006", "name": "Marcel"},
    {"slack_id": "U08H4Q9GK7S", "ma_id": "MA-007", "name": "Sara"},
    # weitere Mitarbeiter hier hinzufügen...
]

# ── Slack Client ─────────────────────────────────────────────────
client = WebClient(token=SLACK_BOT_TOKEN)


def sende_fragen(slack_user_id, mitarbeiter_id, name):
    alle_fragen = get_alle_fragen()
    if not alle_fragen:
        print(f"⚠️  Keine aktiven Fragen verfügbar!")
        return

    ausgewaehlte = waehle_fragen(alle_fragen, mitarbeiter_id, FRAGEN_PRO_TAG)

    # Begrüßung + alle Fragen in einer Nachricht
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Guten Morgen, *{name}*! 👋\nHier sind deine *{FRAGEN_PRO_TAG} Lernfragen* für heute.\nEinfach auf eine Antwort klicken – du bekommst sofort Feedback!"
            }
        },
        {"type": "divider"}
    ]

    for i, frage in enumerate(ausgewaehlte, 1):
        blocks.extend(baue_frage_block(frage, i, FRAGEN_PRO_TAG))
        if i < len(ausgewaehlte):
            blocks.append({"type": "divider"})

    try:
        client.chat_postMessage(
            channel=slack_user_id,
            blocks=blocks,
            text=f"📚 Deine {FRAGEN_PRO_TAG} Lernfragen für heute"
        )
        print(f"✅ Gesendet an {name}")
    except SlackApiError as e:
        print(f"❌ Fehler für {name}: {e.response['error']}")


if __name__ == "__main__":
    print(f"🚀 Täglicher Versand an {len(MITARBEITER)} Mitarbeiter...")
    for ma in MITARBEITER:
        sende_fragen(ma["slack_id"], ma["ma_id"], ma["name"])
        time.sleep(1)   # Slack Rate Limit
    print("✅ Fertig!")
