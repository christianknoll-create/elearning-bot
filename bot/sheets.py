"""
Gemeinsame Google Sheets Logik.
Wird von send_daily.py und webhook.py genutzt.
"""

import os, json, random
from datetime import datetime, date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_NAME = "elearning_google_drive"
SHEET_FRAGEN     = "📚 Fragen-Bank"
SHEET_TRACKING   = "📊 Mitarbeiter-Tracking"


def get_sheets_client():
    """Verbindung zu Google Sheets herstellen."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    # Credentials kommen aus der Umgebungsvariable (GitHub Secret / Railway Variable)
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON nicht gesetzt!")

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    return gc.open(SPREADSHEET_NAME)


def get_alle_fragen():
    """Alle aktiven und geprüften Fragen laden."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_FRAGEN)
    records = sheet.get_all_records(expected_headers=[
    "Frage-ID", "Status", "Themenbereich", "Schwierigkeitsgrad",
    "Fragestellung", "Antwort A", "Antwort B", "Antwort C", "Antwort D",
    "Korrekte Antwort", "Erklärung A", "Erklärung B", "Erklärung C", "Erklärung D",
    "Confluence-Quelle", "Erstellt am", "Geprüft"
    ])
    return [r for r in records if r.get("Status") == "Aktiv" and r.get("Geprüft") == "Ja"]


def get_mitarbeiter_fehler(mitarbeiter_id):
    """Fehler-Häufigkeit pro Thema für adaptives Lernen."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_TRACKING)
    records = sheet.get_all_records()
    fehler = {}
    for r in records:
        if str(r.get("Mitarbeiter-ID")) == str(mitarbeiter_id) and r.get("Richtig?") == "Nein":
            thema = r.get("Themenbereich", "")
            fehler[thema] = fehler.get(thema, 0) + 1
    return fehler


def waehle_fragen(alle_fragen, mitarbeiter_id, anzahl=3):
    """Adaptiv Fragen auswählen – Fehler-Themen werden bevorzugt."""
    fehler = get_mitarbeiter_fehler(mitarbeiter_id)
    gewichtet = []
    for frage in alle_fragen:
        thema = frage.get("Themenbereich", "")
        gewicht = 1 + fehler.get(thema, 0) * 2
        gewichtet.extend([frage] * gewicht)

    ausgewaehlt = []
    ids_gewaehlt = set()
    random.shuffle(gewichtet)
    for frage in gewichtet:
        fid = frage.get("Frage-ID")
        if fid not in ids_gewaehlt:
            ausgewaehlt.append(frage)
            ids_gewaehlt.add(fid)
        if len(ausgewaehlt) == anzahl:
            break
    return ausgewaehlt


def log_antwort(mitarbeiter_id, name, frage_id, thema, schwierigkeit,
                gegebene_antwort, korrekte_antwort, antwortzeit_sek):
    """Antwort ins Tracking-Sheet schreiben."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_TRACKING)
    alle = sheet.get_all_values()
    log_id = f"L-{len(alle):04d}"
    richtig = "Ja" if gegebene_antwort == korrekte_antwort else "Nein"

    sheet.append_row([
        log_id,
        date.today().strftime("%Y-%m-%d"),
        datetime.now().strftime("%H:%M:%S"),
        mitarbeiter_id, name, frage_id,
        thema, schwierigkeit,
        gegebene_antwort, korrekte_antwort,
        richtig, antwortzeit_sek, 1, ""
    ])
    print(f"✅ Log: {log_id} | {name} | {frage_id} | {richtig}")
