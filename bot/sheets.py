"""
Gemeinsame Google Sheets Logik.
"""

import os, json, random
from datetime import datetime, date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_FRAGEN      = "📚 Fragen-Bank"
SHEET_TRACKING    = "📊 Mitarbeiter-Tracking"
SHEET_MITARBEITER = "👥 Mitarbeiter"


def get_sheets_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON nicht gesetzt!")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    print(f"ID: '{os.environ.get('SPREADSHEET_ID')}'")
    return gc.open_by_key(os.environ.get("SPREADSHEET_ID"))


def get_alle_fragen():
    """Alle aktiven Fragen laden."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_FRAGEN)
    records = sheet.get_all_records()
    return [r for r in records if r.get("Status") == "Aktiv"]


def get_mitarbeiter_liste():
    """Mitarbeiterliste aus Google Sheets laden."""
    try:
        book = get_sheets_client()
        sheet = book.worksheet(SHEET_MITARBEITER)
        records = sheet.get_all_records()
        return [r for r in records if r.get("Aktiv", "Ja") == "Ja"]
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mitarbeiter: {e}")
        return []


def add_mitarbeiter(slack_id, ma_id, name):
    """Neuen Mitarbeiter ins Sheet eintragen."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_MITARBEITER)
    sheet.append_row([slack_id, ma_id, name, "Ja", date.today().strftime("%Y-%m-%d")])
    print(f"✅ Mitarbeiter hinzugefügt: {name}")


def remove_mitarbeiter(slack_id):
    """Mitarbeiter deaktivieren (nicht löschen)."""
    book = get_sheets_client()
    sheet = book.worksheet(SHEET_MITARBEITER)
    records = sheet.get_all_records()
    for i, r in enumerate(records, 2):  # Zeile 1 = Header
        if r.get("Slack-ID") == slack_id:
            sheet.update_cell(i, 4, "Nein")  # Spalte D = Aktiv
            print(f"✅ Mitarbeiter deaktiviert: {r.get('Name')}")
            return r.get("Name")
    return None


def get_wiederholungs_fragen(mitarbeiter_id, alle_fragen):
    """
    Gibt Fragen zurück die wiederholt werden müssen:
    - Zuletzt falsch beantwortet
    - Noch nicht 2x hintereinander richtig
    """
    try:
        book = get_sheets_client()
        sheet = book.worksheet(SHEET_TRACKING)
        records = sheet.get_all_records()

        # Nur Einträge dieses Mitarbeiters, nach Datum sortiert
        ma_records = [r for r in records if str(r.get("Mitarbeiter-ID")) == str(mitarbeiter_id)]

        # Pro Frage: letzten 2 Antworten prüfen
        frage_history = {}
        for r in ma_records:
            fid = r.get("Frage-ID")
            if fid:
                if fid not in frage_history:
                    frage_history[fid] = []
                frage_history[fid].append(r.get("Richtig?", "Nein"))

        # Fragen die wiederholt werden müssen
        wiederholung_ids = set()
        for fid, history in frage_history.items():
            letzte_zwei = history[-2:]
            # Wiederholen wenn letzte Antwort falsch ODER nicht 2x hintereinander richtig
            if letzte_zwei[-1] == "Nein" or letzte_zwei != ["Ja", "Ja"]:
                if letzte_zwei[-1] == "Nein":  # Nur wenn zuletzt falsch
                    wiederholung_ids.add(fid)

        # Passende Fragen aus der Fragen-Bank zurückgeben
        wiederholungs_fragen = [f for f in alle_fragen if f.get("Frage-ID") in wiederholung_ids]
        return wiederholungs_fragen

    except Exception as e:
        print(f"⚠️ Wiederholungs-Check Fehler: {e}")
        return []


def get_mitarbeiter_fehler(mitarbeiter_id):
    """Fehler-Häufigkeit pro Thema für adaptives Lernen."""
    try:
        book = get_sheets_client()
        sheet = book.worksheet(SHEET_TRACKING)
        records = sheet.get_all_records()
        fehler = {}
        for r in records:
            if str(r.get("Mitarbeiter-ID")) == str(mitarbeiter_id) and r.get("Richtig?") == "Nein":
                thema = r.get("Themenbereich", "")
                fehler[thema] = fehler.get(thema, 0) + 1
        return fehler
    except Exception:
        return {}


def waehle_fragen(alle_fragen, mitarbeiter_id, anzahl=3):
    """
    Adaptiv Fragen auswählen:
    1. Zuerst: Wiederholungsfragen (zuletzt falsch beantwortet)
    2. Dann: neue Fragen, Fehler-Themen bevorzugt
    """
    # Wiederholungsfragen haben Vorrang
    wiederholungen = get_wiederholungs_fragen(mitarbeiter_id, alle_fragen)
    fehler = get_mitarbeiter_fehler(mitarbeiter_id)

    ausgewaehlt = []
    ids_gewaehlt = set()

    # Erst Wiederholungsfragen einplanen (max. 2 pro Tag)
    random.shuffle(wiederholungen)
    for frage in wiederholungen[:2]:
        fid = frage.get("Frage-ID")
        if fid not in ids_gewaehlt:
            ausgewaehlt.append(frage)
            ids_gewaehlt.add(fid)
        if len(ausgewaehlt) == anzahl:
            break

    # Rest mit gewichteten neuen Fragen auffüllen
    if len(ausgewaehlt) < anzahl:
        gewichtet = []
        for frage in alle_fragen:
            if frage.get("Frage-ID") in ids_gewaehlt:
                continue
            thema = frage.get("Themenbereich", "")
            gewicht = 1 + fehler.get(thema, 0) * 2
            gewichtet.extend([frage] * gewicht)

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
    try:
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
    except Exception as e:
        print(f"❌ Fehler beim Loggen: {e}")
