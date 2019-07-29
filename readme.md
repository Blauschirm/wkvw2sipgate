# Overview

This program aims to crawl a timetable of phone dates and transfer those via the sipgate api into the telefon system.

## Aufgabe

Die NFS bietet 3 Telefonnummern an die ständig besetzt sein sollen.
Die Telefonnummern bleiben immer gleich, aber werden entsprechend dem [Dienstplan](http://notfallplan-dortmund.notfallseelsorge-ekvw.de) umgeleitet.

Es gibt täglich normalerweise zwei Schichten (`20 Uhr - 08 Uhr` und `08 Uhr - 20 Uhr`) für die Personen/Nummern eingetragen sind.

Die Umleitung ist normalerweise für die gesamte Schicht gültig, es gibt aber manchmal bei einer Eintragung Kommentare wie `12:30-16:30 übernimmt Mr. Emil`. Diese müssen berücksichtigt werden und entsprechend gibt es eine temporäre Umleitung der Umleitung.

## sipgate.com
- Telefonnummern buchen
- Weiterleitungen einrichten


## NFS
- 3 Öffentliche Nummern
    - Auf sipgate.com gebucht
    - Weiterleitung wird nach Dienstplan eingerichtet, per API
        - Dienstplan wird mit `beautiful-soup` gecrawled (weil wir leider keinen Zugriff auf die Rohdaten haben)
- `20-8 Uhr` Schicht
        - NB: Geht vom Tag der Eintragung zum nächst Tag! D.h. Am 2.7. um 6 Uhr morgens muss die Nummer vom 1.7. verwendet werden.
- `8-20 Uhr` Schicht


# Installation
- Python3
- BeautifulSoup `python -m pip install beautifulsoup4`
    - `from bs4 import BeautifulSoup`

# config.json
```
{
    "real_base_url" : "echte url",
    "test_base_url" : "test url",

    "schedule_login_payload" : {
        "name": "username",
        "pass": "passwort",
        "form_id": "user_login"
    },

    "SIPGATE_BASE_URL" : "https://api.sipgate.com/v2",
    "SIPGATE_PASS_BASE64_OLD" : "2nd test account for sipgate api",
    "SIPGATE_PASS_BASE64" : "1st test account for sipgate api",

    "NUMBER_MAP" : {
        "NFS1": "Öffentliche Nummer 1", 
        "NFS2": "Öffentliche Nummer 2",
        "Leitung": "Nummer 3? Organisationsprobleme für NFS1/NFS2?"
    }
}
```

# Ideen wie das ganze Funktionieren könnte

Läuft jede volle Stunde - eher alle 5 minuten
Lädt sich alle Daten für den aktuellen und den letzten Monat herunter
Sucht sich den korrekten Zeitslot aus
Schaltet die Rufumleitungen
