"""
webhook.py — läuft dauerhaft auf Railway.
Empfängt Button-Klicks von Slack und sendet Feedback.
"""

import os, json, time
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sheets import log_antwort

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=SLACK_BOT_TOKEN)
app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return "eLearning Bot läuft ✅", 200


@app.route("/slack/interaktiv", methods=["POST"])
def handle_klick():
    payload = json.loads(request.form.get("payload", "{}"))

    if payload.get("type") != "block_actions":
        return jsonify({"status": "ignored"})

    aktion     = payload["actions"][0]
    user       = payload["user"]
    slack_uid  = user["id"]
    user_name  = user.get("name", slack_uid)
    channel_id = payload["container"]["channel_id"]
    message_ts = payload["container"]["message_ts"]

    # Daten aus dem Button lesen
    daten         = json.loads(aktion["value"])
    frage_id      = daten["frage_id"]
    gewaehlt      = daten["gewaehlt"]
    korrekt       = daten["korrekt"]
    erklaerung    = daten.get("erklaerung", "")
    thema         = daten["thema"]
    schwierigkeit = daten["schwierigkeit"]
    antwortzeit   = int(time.time()) - daten.get("ts", int(time.time()))

    richtig = gewaehlt == korrekt

    if richtig:
        feedback = (
            f"✅ *Richtig!* Antwort *{gewaehlt}* ist korrekt. 🎉\n\n"
            f"💡 *Zur Erinnerung:* {erklaerung}" if erklaerung and erklaerung != "— (korrekt)"
            else f"✅ *Richtig!* Antwort *{gewaehlt}* ist korrekt. 🎉"
        )
    else:
        feedback = (
            f"❌ *Leider falsch.* Du hast *{gewaehlt}* gewählt, "
            f"richtig wäre *{korrekt}* gewesen.\n\n"
            f"💡 *Erklärung:* {erklaerung}"
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
