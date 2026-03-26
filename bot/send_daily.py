"""
send_daily.py
─────────────
Wird von GitHub Actions täglich um 09:00 Uhr gestartet.
Mitarbeiterliste kommt aus Google Sheets (👥 Mitarbeiter Tab).
"""

import os, time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sheets import get_alle_fragen, waehle_fragen, get_mitarbeiter_liste
from messages import baue_frage_block

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
FRAGEN_PRO_TAG  = 3
client = WebClient(token=SLACK_BOT_TOKEN)


def sende_fragen(slack_user_id, mitarbeiter_id, name):
    alle_fragen = get_alle_fragen()
    if not alle_fragen:
        print(f"⚠️  Keine aktiven Fragen verfügbar!")
        return

    ausgewaehlte = waehle_fragen(alle_fragen, mitarbeiter_id, FRAGEN_PRO_TAG)

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
    # Mitarbeiterliste aus Google Sheets laden
    mitarbeiter = get_mitarbeiter_liste()

    if not mitarbeiter:
        print("⚠️  Keine Mitarbeiter in Google Sheets gefunden!")
        print("   Tipp: Tab '👥 Mitarbeiter' anlegen mit Spalten: Slack-ID, MA-ID, Name, Aktiv")
        exit(1)

    print(f"🚀 Täglicher Versand an {len(mitarbeiter)} Mitarbeiter...")
    for ma in mitarbeiter:
        sende_fragen(ma["Slack-ID"], ma["MA-ID"], ma["Name"])
        time.sleep(1)
    print("✅ Fertig!")
