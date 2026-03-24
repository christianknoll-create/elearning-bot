"""
Slack Block Kit Nachrichten bauen.
"""

import json, time


def baue_frage_block(frage, frage_nr, gesamt=3):
    """Eine Frage als Slack Block Kit Nachricht bauen."""
    fid       = frage.get("Frage-ID", "")
    fragetext = frage.get("Fragestellung", "")
    thema     = frage.get("Themenbereich", "")
    schwierig = frage.get("Schwierigkeitsgrad", "")
    korrekt   = frage.get("Korrekte\nAntwort", frage.get("Korrekte Antwort", ""))
    erklaerung = frage.get("Erklärung (bei Fehler)", "")

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

    # 4 Antwort-Buttons
    buttons = []
    for key in ["A", "B", "C", "D"]:
        text = frage.get(f"Antwort {key}", "")
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": f"{key}:  {text}", "emoji": True},
            "value": json.dumps({
                "frage_id": fid,
                "gewaehlt": key,
                "korrekt": korrekt,
                "erklaerung": erklaerung,
                "thema": thema,
                "schwierigkeit": schwierig,
                "ts": int(time.time())
            }),
            "action_id": f"antwort_{fid}_{key}"
        })

    blocks.append({"type": "actions", "elements": buttons})
    return blocks
