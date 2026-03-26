"""
Slack Block Kit Nachrichten bauen.
"""

import json, time


def baue_frage_block(frage, frage_nr, gesamt=3):
    fid        = frage.get("Frage-ID", "")
    fragetext  = frage.get("Fragestellung", "")
    thema      = frage.get("Themenbereich", "")
    schwierig  = frage.get("Schwierigkeitsgrad", "")
    korrekt    = frage.get("Korrekte Antwort", "")
    emoji_schwierig = {"Einfach": "🟢", "Mittel": "🟡", "Schwer": "🔴"}.get(schwierig, "⚪")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📚 Frage {frage_nr} von {gesamt}", "emoji": True}
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                "text": f"{emoji_schwierig} *{schwierig}*  |  Thema: *{thema}*  |  `{fid}`"}]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{fragetext}*"}
        },
        {"type": "divider"}
    ]

    # Jede Antwort als eigene Zeile mit Button rechts — besser lesbar bei langen Texten
    for key in ["A", "B", "C", "D"]:
        antworttext = frage.get(f"Antwort {key}", "")
        erklaerung  = frage.get(f"Erklärung {key}", "")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{key}*  –  {antworttext}"
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": f"➤ {key}", "emoji": True},
                "value": json.dumps({
                    "frage_id":   fid,
                    "gewaehlt":   key,
                    "korrekt":    korrekt,
                    "erklaerung": erklaerung,
                    "thema":      thema,
                    "schwierigkeit": schwierig,
                    "ts": int(time.time())
                }),
                "action_id": f"antwort_{fid}_{key}"
            }
        })

    return blocks
