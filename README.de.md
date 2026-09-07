# waipu.tv – Home Assistant Custom Integration

🇬🇧 [English](README.md)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)
[![Validate](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg)](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml)

Inoffizielle Home-Assistant-Integration für [waipu.tv](https://www.waipu.tv/),
einen deutschen IPTV-Streaming-Dienst. Bringt EPG-Daten und Cloud-DVR-Steuerung
nach HA, und koppelt optional mit einer vorhandenen Apple-TV- oder
Android-TV-Integration, um die waipu-App per Knopfdruck auf dem Fernseher zu
starten.

📖 **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** — vollständige
Entity-/Service-Referenz, Android-TV-Senderwechsel im Detail erklärt,
durchgespielte Automations-/Skript-Beispiele, und direkt anpassbare
Dashboard-Karten (dieses README bleibt ein Schnelleinstieg).

> **Haftungsausschluss:** Diese Integration ist **nicht** mit Exaring AG /
> waipu.tv verbunden oder von ihnen unterstützt. Sie nutzt eine
> reverse-engineerte API (ursprünglich erschlossen durch das Kodi-Plugin
> [flubshi/plugin.video.waipu.tv](https://github.com/flubshi/plugin.video.waipu.tv)).
> waipu kann die API jederzeit ändern oder blockieren.

## Was funktioniert — und was nicht

| Funktion | Status |
|---|---|
| Login (Benutzername/Passwort, keine 2FA) | ✅ |
| Senderliste + Sender-Logos | ✅ |
| EPG: laufendes & nächstes Programm pro Sender als Sensor | ✅ |
| Cloud-Aufnahme planen (Button pro Sender + Service) | ✅ (nur Perfect / Perfect Plus / O2 TV L/XL) |
| Aufnahmen auflisten (HA-Kalender) | ✅ |
| Aufnahmen löschen (Service) | ✅ |
| waipu-App auf Apple TV starten | ✅ (nur App-Start — waipu hat keine Sender-Deep-Links) |
| waipu-App auf Android TV starten | ✅ (nur App-Start — waipu hat keine Sender-Deep-Links) |
| Sender auf Android TV wechseln (Service) | ✅ (braucht die richtige *Kanalnummer-Basis*-Einstellung — siehe [Android-TV-Senderwechsel](#android-tv-senderwechsel)) |
| Serien-Aufnahme starten/beenden (Service) | ✅ beide live bestätigt funktionsfähig |
| Stream direkt in HA abspielen | ❌ — durch Widevine-DRM blockiert |

> Die Entity-*Bezeichnungen* der Integration sind aktuell auf Deutsch (`jetzt`, `danach`, `aufnahmen`, `wiedergabe`, …). Der Code selbst ist auf Englisch; eine Lokalisierung könnte bei Bedarf später nachgezogen werden.

## Installation

### Option 1: HACS Custom Repository (empfohlen)

Ein-Klick-Installation über den Badge oben in diesem README — öffnet HACS auf
deiner Home-Assistant-Instanz und registriert dieses Repository direkt.

Oder manuell:

1. HACS → Drei-Punkte-Menü → *Benutzerdefinierte Repositories*
2. URL: `https://github.com/KindOfNerdy/ha-waipu`, Kategorie *Integration*
3. **waipu.tv** installieren, Home Assistant neu starten

### Option 2: Manuelle Installation

Den Ordner `custom_components/waipu/` in dein Home-Assistant-Konfigurationsverzeichnis kopieren:

```
<HA-config>/custom_components/waipu/
```

Danach Home Assistant neu starten.

## Einrichtung

1. *Einstellungen* → *Geräte & Dienste* → *Integration hinzufügen* → **waipu.tv**
2. waipu-E-Mail + Passwort eingeben (wird nur zum Login genutzt — erscheint
   nirgends in der UI; der Eintrag wird nach deinem Abo-Namen benannt, sobald
   der bekannt ist, z. B. "Perfect Plus", nicht nach deiner E-Mail)
3. Der Einrichtungsassistent fragt direkt danach, ob ein **Apple TV**
   und/oder **Android TV** gekoppelt werden soll:
   - **Apple-TV media_player** — deine vorhandene Apple-TV-Entity, z. B.
     `media_player.wohnzimmer_apple_tv`
   - **Apple-TV remote** — die passende remote-Entity, optional zum Senden
     eigener Tastenfolgen aus eigenen Skripten
   - **Android-TV remote-Entity** — deine vorhandene `remote.*`-Entity aus der
     offiziellen [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)-Integration,
     z. B. `remote.wohnzimmer_android_tv`

   Alle drei Felder sind optional und unabhängig voneinander — richte
   eins, beide oder keins ein, dieser Schritt kann auch einfach
   übersprungen werden (leeres Formular absenden). Alles hier lässt sich
   auch später noch nachtragen oder ändern, siehe Schritt 4.
4. Nach Abschluss der Einrichtung jederzeit *Konfigurieren* (Optionen)
   öffnen, um obiges zu ändern oder die weiteren, fortgeschritteneren
   Optionen einzustellen:
   - **Sichtbare Sender** — begrenzt, welche Sender HA-Entities bekommen (ein
     volles waipu-Paket kann 300+ Sender bedeuten — nur die auswählen, die dich interessieren)
   - **waipu-App Bundle-ID** — Standard `de.exaring.waipu.tvos`. Falls
     falsch, die echte Bundle-ID mit pyatv vom Apple TV auslesen:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```
   - **waipu-App-Link** — Standard `waipu://tv` (öffnet die Live-TV-Ansicht der
     App). Der Start per reiner Package-ID (z. B. `de.exaring.waipu`) ist seit
     einer Google-Play-Store-Änderung unzuverlässig — siehe die
     [androidtv_remote-Dokumentation](https://www.home-assistant.io/integrations/androidtv_remote/)
     — deshalb wird standardmäßig ein Deep-Link genutzt. Überschreibe das, wenn
     du lieber auf einem anderen Bereich landen willst (z. B. `waipu://epg`,
     `waipu://recordings`) oder dein Gerät einen anderen Wert braucht (z. B.
     für `o2 TV powered by waipu.tv`).
   - **Kanalnummer-Basis** — `Nur Favoriten` (Standard) oder `Alle Sender`.
     Nur relevant für den
     [Senderwechsel](#android-tv-senderwechsel)-Service. Bei
     `Nur Favoriten` folgen außerdem alle von der Integration angelegten
     HA-Entities (Sensoren, Aufnahme-Buttons, die Sender-Liste des
     media_players) live deinen waipu-Favoriten — "Sichtbare Sender" wird in
     diesem Modus ignoriert.
   - **Wartezeit vor Senderwahl auf Android TV** — Standard 4 Sekunden.
     `remote.turn_on` bestätigt nur den Einschaltzustand des Fernsehers, nicht
     dass die waipu-App tatsächlich fertig gestartet ist und Zifferneingaben
     annimmt — bei zu kurzer Wartezeit werden die Ziffern stillschweigend
     ignoriert. Erhöhe den Wert, falls das Umschalten direkt nach einem
     Kaltstart (TV/App war komplett aus) nicht auf dem richtigen Sender landet;
     ein schneller App-Wechsel bei bereits eingeschaltetem Fernseher braucht
     deutlich weniger Zeit, aber dieselbe Wartezeit gilt aktuell für beide Fälle.
   - **EPG-Cache-Gültigkeit** — Standard 60 Minuten, 0 deaktiviert das
     Caching. Jeder abgerufene EPG-Grid-Slot (ein 4h-Block) wird so lange
     wiederverwendet, statt bei jedem 5-Minuten-Poll neu bei waipu
     angefragt zu werden — reduziert die Request-Zahl deutlich, ohne
     einen einzelnen Poll größer zu machen. Beeinflusst nicht, welches
     Programm als "jetzt"/"danach" angezeigt wird — das wird immer gegen
     die echte aktuelle Uhrzeit berechnet. Einziger Trade-off: Eine
     kurzfristige Programmänderung (z. B. Sport läuft länger) kann bis zu
     dieser Zeit brauchen, um lokal anzukommen.

## Android TV

Der Start der waipu-App auf Android TV läuft komplett über Home Assistants
offizielle [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)-Integration
— diese Integration ruft nur diese auf, spricht nicht selbst mit dem
Fernseher. Bevor du die obigen Felder konfigurierst, stell sicher:

1. Die waipu-App ist bereits auf dem Android TV installiert (Play Store).
2. Die `androidtv_remote`-Integration ist in Home Assistant eingerichtet und
   mit dem Fernseher gekoppelt — das ergibt eine `remote.*`-Entity dafür.

Dann **Android-TV remote-Entity** auf genau diese `remote.*`-Entity zeigen
lassen. Die alte ADB-basierte `androidtv`-Integration wird **nicht**
unterstützt — sie ist unmaintained und für diesen Zweck weniger zuverlässig;
nutze `androidtv_remote`.

Wie bei Apple TV ist das nur ein App-Start: waipu bietet auch auf Android TV
keinen sender-spezifischen Deep-Link, der Sender muss also nach dem Start
manuell auf dem Fernseher gewählt werden.

## Android-TV-Senderwechsel

`waipu.switch_channel_on_android_tv` kann den Sender tatsächlich wechseln —
indem die auf dem Bildschirm angezeigte Kanalnummer als Zifferntasten-Eingabe
per `remote.send_command` gesendet wird (`androidtv_remote` stellt echte
Android-TV-Fernbedienungs-Keycodes `"0"`–`"9"` bereit), genau wie mit dem
Zifferblock einer physischen Fernbedienung.

**So wird die Kanalnummer ermittelt:** waipu liefert keine Kanalnummer über
seine API — die in der App angezeigte Nummer ist einfach die Position des
Senders in deiner eigenen Senderliste (1. Sender → `1`, 8. Sender → `8`,
usw.), bestätigt durch Abgleich der API-Senderreihenfolge mit der
On-Screen-Nummerierung der App. Diese Integration berechnet diese Position
live aus derselben Listenreihenfolge, die die API ohnehin liefert, basierend
auf der Option **Kanalnummer-Basis** (`Alle Sender` oder `Nur Favoriten`).

**Das funktioniert nur, wenn diese Einstellung zu dem passt, was die
waipu-App auf deinem Android TV gerade anzeigt.** Ob die App alle Sender
oder nur Favoriten zeigt, ist eine App-seitige Einstellung — Home Assistant
kann sie nicht auslesen oder ändern. Stimmen beide nicht überein, schaltet
der Service stillschweigend auf den *falschen* Sender (welche Nummer N in
der aktuell aktiven Ansicht der App auch immer ist) — es gibt keinen
Rückmeldeweg, mit dem HA das erkennen könnte. Wähle den Modus, den du auf
diesem Fernseher tatsächlich nutzt, und halte ihn konsistent mit der Option
"Kanalnummer-Basis".

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # erforderlich — die waipu-Sender-ID, zu der gewechselt werden soll
```

Angesichts der oben beschriebenen App-Zustands-Abhängigkeit: bitte als
Best-Effort-Funktion behandeln, nicht als zuverlässigen Senderwechsler.

## Erzeugte Entities

Vollständige Attribut-Referenz: siehe das
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.
Die Entities landen auf einem von drei Geräten; die genauen Entity-IDs hängen
von deiner Einrichtungs-Historie ab (das Umbenennen eines Geräts benennt
bereits angelegte Entity-IDs nicht um), die unten genannten also als
Beispiel verstehen — die tatsächlichen unter *Entwicklerwerkzeuge →
Zustände* nachschauen.

**waipu Senderübersicht** (ein Satz pro ausgewähltem Sender):

- `sensor.<sender>_jetzt` / `_danach` — Titel des aktuellen/nächsten Programms
  als Zustand, mit EPG-Details (`description`, `parental_guidance`/FSK,
  `rerun`, Episoden-/Genre-Infos) als Attribute. `_danach` listet zusätzlich
  weitere `upcoming`-Programme (mit `program_id`, `episode_title` und
  `series_id`, nutzbar mit `waipu.create_recording`/
  `waipu.create_serial_recording`, um etwas später als "jetzt"
  aufzunehmen).
- ein Button pro Sender — nimmt auf, was gerade läuft (nur bei
  DVR-fähigem Abo).

**waipu Wiedergabe** (TV-Steuerung):

- die `media_player`-Entity — startet/steuert, welcher Fernseher auch immer
  konfiguriert ist (Apple TV hat Vorrang, falls beide gesetzt sind — nutze
  die dedizierten Services, um gezielt eins der beiden anzusprechen);
  `state`, Lautstärke und Quelle folgen live dem echten Fernseher. Auf
  Android TV wechseln die Weiter-/Zurück-Tasten der Karte den Sender —
  siehe [Android-TV-Senderwechsel](#android-tv-senderwechsel).
- ein reines Sender-`select`-Dropdown, unabhängig vom media_player — praktisch,
  wenn dein Dashboard schon den nativen media_player des Fernsehers für
  Ein/Aus, Lautstärke und andere Apps wie Netflix nutzt.
- Drei Android-TV-exklusive Shortcut-Buttons, um direkt in die
  TV-/EPG-/Aufnahmen-Ansicht der App zu springen.

**waipu Aufnahmen** (Aufnahme-Verwaltung, nur bei DVR-fähigem Abo):

- der Aufnahmen-`calendar` — jede geplante/laufende/fertige Aufnahme, mit
  Angesehen-Status und vollem EPG-Text, wo verfügbar.
- zwei Sensoren — Anzahl ungesehener / gesamter Aufnahmen, jeweils mit einer
  `recordings`-Liste als Attribut.

## Services

Vollständige Referenz mit mehr Beispielen:
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

```yaml
service: waipu.create_recording
data:
  station_id: ard          # erforderlich (waipu-Sender-ID, kleingeschrieben)
  program_id: "67ad0d26-…" # optional, UUID — Standard: aktuell laufendes Programm

service: waipu.delete_recording
data:
  recording_id: "1206434822"   # einzelne ID oder Liste

service: waipu.create_serial_recording   # bestätigt funktionsfähig — siehe Wiki
data:
  station_id: ard
  program_id: "67ad0d26-…"   # optional — Standard: aktuell laufendes Programm

service: waipu.delete_serial_recording   # bestätigt funktionsfähig — siehe Wiki
data:
  series_id: "104121"   # aus dem series_id-Attribut eines Sensors

service: waipu.launch_on_apple_tv
# nutzt das in den Integrations-Optionen konfigurierte Apple TV

service: waipu.launch_on_android_tv
# nutzt das in den Integrations-Optionen konfigurierte Android TV

service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # siehe Abschnitt oben
```

## Dashboard-Beispiel

Die Entity-IDs unten an deine eigenen anpassen (siehe Hinweis bei *Erzeugte Entities*):

```yaml
type: entities
title: waipu
entities:
  - entity: media_player.waipu_wiedergabe
  - entity: sensor.ard_jetzt
    secondary_info: last-changed
  - entity: button.ard_aktuelles_programm_aufnehmen
  - entity: calendar.waipu_aufnahmen
```

## Bekannte Einschränkungen

- **Kein sender-spezifischer Deep-Link.** Weder die waipu-tvOS- noch die
  waipu-Android-TV-App bieten einen öffentlichen *Deep-Link* zum
  Senderwechsel. Nach dem App-Start muss der Sender auf Apple TV manuell
  gewählt werden. Auf Android TV gibt es einen funktionierenden Workaround
  über Zifferntasten-Eingabe — siehe
  [Android-TV-Senderwechsel](#android-tv-senderwechsel) — der
  aber von einer App-seitigen Anzeige-Einstellung abhängt, die HA nicht
  prüfen kann; als Best-Effort behandeln, nicht als garantierten
  Senderwechsler.
- **Keine 2FA.** waipu unterstützt aktuell nur reinen Passwort-Login; sollte
  2FA für dein Konto irgendwann aktiviert werden, müsste der Ablauf hier
  überarbeitet werden.
- **API-Änderungen.** waipu hat schon mehrfach ältere App-Versionen
  serverseitig blockiert. Falls die Integration plötzlich nichts mehr
  liefert, zuerst nach einem Update in diesem Repo schauen.
- **Serien-Aufnahme wurde per Reverse-Engineering gebaut, inzwischen bestätigt.**
  `waipu.create_serial_recording` und `waipu.delete_serial_recording`
  wurden beide komplett anhand von Anfrage-Beispielen im Web-Client von
  waipu nachgebaut, ohne je eine echte Antwort gesehen zu haben — beide
  sind inzwischen live bestätigt: `create_serial_recording` ließ die
  waipu-App die Aufnahmen der Serie sofort als laufend anzeigen, und
  `delete_serial_recording` (inklusive des Toggles "bereits
  heruntergeladene Folgen mitlöschen") hat sie korrekt gestoppt und wieder
  entfernt.

## Lizenz

GPL-3.0 (übernommen aus der Kodi-Plugin-Abstammung). Siehe [LICENSE](LICENSE).
