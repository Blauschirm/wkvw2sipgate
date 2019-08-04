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
- [API Documentation](https://api.sipgate.com/v2/doc#/)
- [Administration Web UI](https://app.sipgate.com/w0/team/settings/phonenumbers)

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
- `beautifulsoup4` to crawl the HTML website for the time schedule
    - `python -m pip install beautifulsoup4`
    - `from bs4 import BeautifulSoup`
- `phonenumbers` to parse phone numbers

## For devs also
- `pytest` to run unit tests

# Run
- Set `TESTING` to true or false
  - If `True` make sure to start the webserver via `dummy_dienstplan/start_dummy_server.bat`
- Configure via `config.json`
- Run `python crawler.py`
- Look at the ouptut, there may be errors and warnings :)

## Running tests
`pytest -vv`

# Configuration: `config.json`
[config.example.json](./config.example.json) nach `config.json` kopieren und Werte in `[eckigen Klammern]` ersetzen.

# Ideen wie das ganze Funktionieren könnte
- Läuft jede volle Stunde - eher alle 5 minuten
- Lädt sich alle Daten für den aktuellen und den letzten Monat herunter
- Sucht sich den korrekten Zeitslot aus
- Schaltet die Rufumleitungen


# Trying to understand SIPGATE

### Anschlüsse
Private nummern, müssen nur eingetragen werden

### Rufnummern
Öffentlich, muss gebucht werden von SIPGATE

### Telefone
- Externe Telefone (private telefonnummern eintragen)
    - Max Mustermann Mobil
        - Absendernummer: Öffentliche nummer von SIPGATE
        - Rufnummer: Private nummer von Max
- Mobiltelefone (SIM-card von sipgate erhalten)
    - Mobiltelefon von Maximilian Botschen
- Telefone (VoIP für sipgate konfiguriert)

## Zusammengefasst
- Account `w0` hat `3` Rufnummern
- Die Rufnummern sind je einem Anschluss zugewiesen (manche haben auch denselben Anschluss)
- Jedem Anschluss sind Geräte zugewiesen
- Jedes Gerät hat eine Nummer (Sidebar entry `Telefone`)

### Appendix

Rufnummer -> Anschluss -> Gerät -> Nummer

|User Interface DE|API               | id   | url |
|-----------------|------------------|---   |--|
|Anschluss        | activePhonelines | `p0` | `GET /{userid}/phonelines` | 
|                 | numbers          |      | `GET /numbers` `GET /{userId}/numbers`|
