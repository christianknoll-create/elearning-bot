"""
webhook.py — läuft dauerhaft auf Railway.
Empfängt Button-Klicks und Admin-Befehle von Slack.
Admin-Befehle nur im privaten Admin-Channel.
"""

import os, json, time
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sheets import log_antwort, add_mitarbeiter, remove_mitarbeiter, get_mitarbeiter_liste

SLACK_BOT_TOKEN  = os.environ["SLACK_BOT_TOKEN"]
ADMIN_CHANNEL_ID = os.environ.get("ADMIN_CHANNEL_ID", "")

client = WebClient(token=SLACK_BOT_TOKEN)
app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return "eLearning Bot läuft ✅", 200


@app.route("/slack/events", methods=["POST"])
def handle_events():
    data = request.json

    # Slack URL Verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})

    # Nur Nachrichten verarbeiten
    if event.get("type") != "message" or event.get("subtype"):
        return jsonify({"status": "ignored"})

    channel = event.get("channel", "")
    text    = event.get("text", "").strip()

    # Nur im Admin-Channel reagieren
    if channel != ADMIN_CHANNEL_ID:
        return jsonify({"status": "ignored"})

    # Befehl: /add SLACK_ID MA-ID Name
    if text.startswith("/add "):
        parts = text[5:].split(" ", 2)
        if len(parts) < 3:
            client.chat_postMessage(channel=channel,
                text="❌ Format: `/add SLACK_ID MA-ID Name`\nBeispiel: `/add U012AB3CD MA-010 Max Mustermann`")
        else:
            slack_id, ma_id, name = parts
            add_mitarbeiter(slack_id, ma_id, name)
            client.chat_postMessage(channel=channel,
                text=f"✅ *{name}* wurde hinzugefügt!\nSlack-ID: `{slack_id}` | MA-ID: `{ma_id}`")

    # Befehl: /remove SLACK_ID
    elif text.startswith("/remove "):
        slack_id = text[8:].strip()
        name = remove_mitarbeiter(slack_id)
        if name:
            client.chat_postMessage(channel=channel,
                text=f"✅ *{name}* wurde deaktiviert.")
        else:
            client.chat_postMessage(channel=channel,
                text=f"❌ Kein Mitarbeiter mit Slack-ID `{slack_id}` gefunden.")

    # Befehl: /liste
    elif text.startswith("/liste"):
        mitarbeiter = get_mitarbeiter_liste()
        if not mitarbeiter:
            client.chat_postMessage(channel=channel,
                text="📋 Keine Mitarbeiter eingetragen.")
        else:
            zeilen = [
                f"*{i+1}.* {m['Name']} | `{m['Slack-ID']}` | {m['MA-ID']} | {'✅ Aktiv' if m.get('Aktiv') == 'Ja' else '❌ Inaktiv'}"
                for i, m in enumerate(mitarbeiter)
            ]
            client.chat_postMessage(channel=channel,
                text=f"📋 *Mitarbeiterliste ({len(mitarbeiter)} Personen):*\n\n" + "\n".join(zeilen))

    # Befehl: /hilfe
    elif text.startswith("/hilfe") or text.startswith("/help"):
        client.chat_postMessage(channel=channel, text=(
            "*eLearning Bot Admin-Befehle:*\n\n"
            "`/add SLACK_ID MA-ID Name` — Mitarbeiter hinzufügen\n"
            "`/remove SLACK_ID` — Mitarbeiter deaktivieren\n"
            "`/liste` — Alle Mitarbeiter anzeigen\n\n"
            "*Slack-ID herausfinden:* Profil anzeigen → (...) → Member-ID kopieren"
        ))

    else:
        client.chat_postMessage(channel=channel,
            text="❓ Unbekannter Befehl. Schreibe `/hilfe` für eine Übersicht.")

    return jsonify({"status": "ok"})


@app.route("/slack/interaktiv", methods=["POST"])
def handle_klick():
    """Antwort-Button wurde geklickt."""
    payload = json.loads(request.form.get("payload", "{}"))

    if payload.get("type") != "block_actions":
        return jsonify({"status": "ignored"})

    aktion     = payload["actions"][0]
    user       = payload["user"]
    slack_uid  = user["id"]
    user_name  = user.get("name", slack_uid)
    channel_id = payload["container"]["channel_id"]
    message_ts = payload["container"]["message_ts"]

    daten         = json.loads(aktion["value"])
    frage_id      = daten["frage_id"]
    gewaehlt      = daten["gewaehlt"]
    korrekt       = daten["korrekt"]
    erklaerung    = daten.get("erklaerung", "").replace("— (korrekt)", "").strip()
    thema         = daten["thema"]
    schwierigkeit = daten["schwierigkeit"]
    antwortzeit   = int(time.time()) - daten.get("ts", int(time.time()))

    richtig = gewaehlt == korrekt

    if richtig:
        feedback = (
            f"✅ *Richtig!* Antwort *{gewaehlt}* ist korrekt. 🎉\n\n"
            f"💡 *Zur Erinnerung:* {erklaerung}"
        )
    else:
        feedback = (
            f"❌ *Leider falsch.* Du hast *{gewaehlt}* gewählt, "
            f"richtig wäre *{korrekt}* gewesen.\n\n"
            f"💡 *Erklärung:* {erklaerung}\n\n"
            f"🔁 _Diese Frage wird dir morgen nochmal gestellt._"
        )

    try:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=message_ts,
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": feedback}},
                {"type": "context", "elements": [{"type": "mrkdwn",
                    "text": f"Thema: *{thema}*  |  Antwortzeit: {antwortzeit}s  |  `{frage_id}`"}]}
            ],
            text=feedback
        )
    except SlackApiError as e:
        print(f"❌ Feedback-Fehler: {e.response['error']}")

    log_antwort(slack_uid, user_name, frage_id, thema, schwierigkeit,
                gewaehlt, korrekt, antwortzeit)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"🌐 Webhook läuft auf Port {port}")
    app.run(host="0.0.0.0", port=port)
