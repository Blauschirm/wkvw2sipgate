# ToDo
- [ ] Logging
- [ ] E-Mails (mailgun)
  - [ ] Fehlermeldungen auch schon für den nächsten Tag
  - [ ] Bestätigung für (vielleicht nur virtuelle/dry-run) Umleitungen -> Simulationsfunktion
      - [ ] config.jons: dryrun: Benutzt sipgate api nicht.
- [ ] In Funktionen/Klassen verpacken
    - [x] `sipgate_api.py`
    - [x] `parser.py`
    - [ ] crawler.py
- [ ] Tests
    - [ ] Integrationstests
    - [ ] Input: liste von datums, url, website
    - [ ] Expected output: Liste von timeslots
- [x] config.json nur einmal gelesen wird, der rest wird dann injected
- [ ] parser.py benutzen? Freitextfeld/Infofeld (i) auslesen und anwenden
- [ ] Fix Day=1 before 8am bug (e.g. datetime.datetime.now() - datetime.timedelta(days = 1))

