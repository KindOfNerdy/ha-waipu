<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/KindOfNerdy/ha-waipu/main/custom_components/waipu/brand/dark_logo@2x.png">
    <img alt="waipu.tv" src="https://raw.githubusercontent.com/KindOfNerdy/ha-waipu/main/custom_components/waipu/brand/logo@2x.png" width="360">
  </picture>
</p>

<h3 align="center">Home-Assistant-Integration für waipu.tv</h3>

<p align="center">
  EPG, Cloud-Aufnahmen und Fernsehersteuerung — auf Android TV direkt auf den Sender oder in die Aufnahme.
</p>

<p align="center">
  <a href="https://github.com/KindOfNerdy/ha-waipu/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/KindOfNerdy/ha-waipu?label=Release"></a>
  <img alt="Home Assistant 2025.8+" src="https://img.shields.io/badge/Home%20Assistant-2025.8%2B-41BDF5?logo=homeassistant&logoColor=white">
  <a href="https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml"><img alt="Validate" src="https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg"></a>
</p>

<p align="center">
  🇬🇧 <a href="README.en.md">English</a> · 📖 <a href="https://github.com/KindOfNerdy/ha-waipu/wiki">Wiki</a>
</p>

---

> **Haftungsausschluss:** Diese Integration ist **nicht** mit Exaring AG /
> waipu.tv verbunden oder von ihnen unterstützt. Sie nutzt eine
> reverse-engineerte API (ursprünglich erschlossen durch das Kodi-Plugin
> [flubshi/plugin.video.waipu.tv](https://github.com/flubshi/plugin.video.waipu.tv)).
> waipu kann die API jederzeit ändern oder blockieren.

## Highlights

- 📺 **Sender direkt umschalten** auf Android TV — aus dem Medien-Browser, dem
  Auswahl-Menü, mit Weiter/Zurück oder per Service, auch bei laufender App
- 🎬 **Aufnahmen am Fernseher abspielen** — im Medien-Browser antippen und
  weiterschauen, wo du aufgehört hast
- 🗓️ **EPG als Sensoren** — was läuft jetzt und danach, pro Sender, mit Bild
- ⏺️ **Cloud-Aufnahmen** planen, stoppen, löschen, ganze Serien aufnehmen —
  plus Aufnahmen-Kalender
- 🎛️ **Alles von der Fernbedienungs-Karte** — Quellen Live-TV, Aufnahmen und
  EPG springen direkt in den jeweiligen Bereich der waipu-App

Das 📖 **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** hat die
vollständige Entity-/Service-Referenz, Automations-Beispiele und fertige
Dashboard-Karten — dieses README ist der Schnelleinstieg.

## Was funktioniert — und was nicht

| Funktion | Status |
|---|---|
| Login (Benutzername/Passwort, keine 2FA) | ✅ |
| Senderliste + Sender-Logos | ✅ |
| EPG: laufendes & nächstes Programm pro Sender als Sensor | ✅ |
| Cloud-Aufnahme planen (Button pro Sender + Service) | ✅ nur Perfect / Perfect Plus / O2 TV L/XL |
| Laufende Aufnahme vorzeitig stoppen, Aufnahmen löschen (Service) | ✅ |
| Serien-Aufnahme starten/beenden (Service) | ✅ |
| Aufnahmen auflisten (HA-Kalender, Sensoren) | ✅ |
| Sender auf Android TV wechseln | ✅ direkt per waipu-Link — siehe [Android-TV-Senderwechsel](#android-tv-senderwechsel) |
| Aufnahme auf Android TV abspielen | ✅ fortsetzen, von vorn oder Detailseite — siehe [Aufnahmen auf Android TV](#aufnahmen-auf-android-tv) |
| waipu-App auf Apple TV starten | ✅ nur App-Start — für tvOS sind keine Sender-Links bekannt |
| Stream direkt in HA abspielen | ❌ durch Widevine-DRM blockiert |

> Die Namen der Entities und Geräte richten sich nach der Sprache deines Home
> Assistant: auf Deutsch z. B. `ARD – jetzt`, auf Englisch `ARD – now`. Die
> Entity-IDs in den Beispielen gehen von einem deutschsprachigen Home
> Assistant aus.

## Installation

Benötigt Home Assistant **2025.8.0** oder neuer.

### Über den Marketplace / HACS (empfohlen)

1. Repository in deinem Home Assistant öffnen:

   [![Repository im Marketplace öffnen](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   <details>
   <summary>Ohne Button</summary>

   Ab Home Assistant 2026.11: *Einstellungen* → *Marketplace* → *Add from
   link*, URL `https://github.com/KindOfNerdy/ha-waipu`, Kategorie
   *Integration*. Bei älteren Versionen mit HACS: HACS → Drei-Punkte-Menü →
   *Benutzerdefinierte Repositories*, gleiche URL und Kategorie.
   </details>

2. **waipu.tv** installieren.
3. Home Assistant neu starten.

### Manuell

Den Ordner `custom_components/waipu/` nach
`<HA-config>/custom_components/waipu/` kopieren und Home Assistant neu
starten.

## Einrichtung

1. Integration hinzufügen:

   [![Integration einrichten](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=waipu)

   oder *Einstellungen* → *Geräte & Dienste* → *Integration hinzufügen* →
   **waipu.tv**.
2. waipu-E-Mail und Passwort eingeben. Sie werden nur zum Login genutzt; der
   Eintrag wird nach deinem Abo benannt (z. B. „Perfect Plus“), nicht nach
   deiner E-Mail.
3. **Fernseher wählen** — Android TV, Apple TV (nur App-Start) oder keiner —
   und auf der nächsten Seite dessen Entity auswählen:
   - **Android TV:** die `remote.*`-Entity aus der offiziellen
     [Android-TV-Remote-Integration](https://www.home-assistant.io/integrations/androidtv_remote/)
     (siehe [Android TV](#android-tv))
   - **Apple TV:** der `media_player` aus der Apple-TV-Integration

Alles lässt sich später unter *Konfigurieren* ändern.

### Optionen

*Konfigurieren* öffnet bis zu drei Seiten: zuerst Fernseher, Senderauswahl
und EPG-Cache, dann die Felder des gewählten Fernsehers, bei „Alle Sender“
zuletzt die Senderliste.

| Option | Bedeutung |
|---|---|
| **Fernseher** | Android TV, Apple TV oder keiner. Es gibt immer genau einen; ein Wechsel entfernt die Einstellungen des bisherigen. |
| **Senderauswahl** | Welche Sender HA-Entities bekommen. `Favoriten` (Standard) folgt live deinen waipu-Favoriten. Bei `Alle Sender` wählst du auf einer eigenen Seite unter **Sichtbare Sender** aus; die Auswahl bleibt gespeichert, auch wenn du zwischendurch auf `Favoriten` wechselst. |
| **EPG-Cache-Gültigkeit** | Standard 60 Minuten, 0 = aus. Spart Anfragen an waipu; „jetzt“/„danach“ stimmen trotzdem immer. Nur kurzfristige Programmänderungen (z. B. Sport läuft länger) kommen bis zu dieser Zeit später an. |
| **waipu-App-Link** (Android TV) | Vorausgefüllt mit `waipu://tv`. Öffnet die App ohne bestimmten Sender. Nur für andere waipu-Varianten (z. B. o2 TV) ändern. |
| **waipu-App Bundle-ID** (Apple TV) | Vorausgefüllt mit `de.exaring.waipu.tvos`. Nur für andere Varianten ändern; auslesen mit `atvremote --id <AppleTV-MAC> apps`. |

## Android TV

Die Integration steuert den Fernseher über Home Assistants offizielle
[Android-TV-Remote-Integration](https://www.home-assistant.io/integrations/androidtv_remote/)
— sie spricht nicht selbst mit dem Gerät. Voraussetzungen:

1. Die waipu-App ist auf dem Android TV installiert.
2. Die Android-TV-Remote-Integration ist eingerichtet und mit dem Fernseher
   gekoppelt — das ergibt die `remote.*`-Entity, die du bei der Einrichtung
   auswählst.

Die alte ADB-basierte `androidtv`-Integration wird **nicht** unterstützt.

Sender und Aufnahmen öffnet die Integration über die Links, die die
waipu-App selbst versteht — dieselben, die sie für ihre Kacheln
„Ihre Lieblingssender“ im Android-TV-Startbildschirm nutzt.

## Android-TV-Senderwechsel

Alle Wege schalten direkt um — egal ob der Fernseher aus ist, gerade eine
andere App läuft oder waipu schon offen ist:

- im **Medien-Browser** des waipu-media_players den Ordner **Sender** öffnen
- das **Sender-Auswahl-Menü** (`select`) nutzen
- **Weiter/Zurück** an der media_player-Karte — nächster/vorheriger Sender
  aus deiner Senderliste, am Ende geht es wieder von vorn los
- der Service:

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # die waipu-Sender-ID, z. B. aus dem station_id-Attribut des media_players
```

Das Umschalten dauert einen kleinen Moment, weil die App den Sender neu
lädt. Die Reihenfolge oder Ansicht in der waipu-App spielt keine Rolle.

## Aufnahmen auf Android TV

Am bequemsten über den **Medien-Browser**: an der media_player-Karte (oder
unter *Medien* in der Seitenleiste) auf „Medien durchsuchen“ tippen.

- **Aufnahmen** — alle fertigen und gerade laufenden Aufnahmen, egal ob
  schon gesehen, neueste zuerst, mit Vorschaubild. Mehrere Folgen derselben
  Serie liegen gesammelt in einem eigenen Ordner; die Serien-Ordner stehen
  oben, nach Titel sortiert. Antippen spielt eine
  Aufnahme am Fernseher ab und setzt dort fort, wo du aufgehört hast —
  komplett gesehene Aufnahmen starten von vorn.
- **Sender** — deine Senderliste; Antippen schaltet um.
- **Programm** — pro Sender die laufende und die kommenden Sendungen der
  nächsten Stunden. Die laufende Sendung antippen spielt sie live ab. Eine
  kommende Sendung öffnet die Auswahl **Details am TV**, **Folge
  aufnehmen** und **Serie aufnehmen** — Aufnehmen läuft direkt über
  waipu, der Fernseher muss dafür nicht an sein. Bereits geplante
  Sendungen sind mit „⏺ geplant“ markiert und bieten **Aufnahme löschen**
  an. Ist Aufnehmen nicht erlaubt (Abo, Sender oder Sendung), öffnet eine
  kommende Sendung direkt ihre Detailseite. Auch bei der laufenden Sendung bietet
  die Detailseite „Restart“ — öffnen lässt sie sich mit dem Service
  `waipu.open_program_on_android_tv`.

Für mehr Kontrolle gibt es den Service:

```yaml
service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"   # aus dem recordings-Attribut der Aufnahmen-Sensoren
  mode: resume                 # resume (Standard) | beginning | details
  # position: 600              # optional: ab Sekunde 600 (hat Vorrang vor mode)
```

| `mode` | Wirkung |
|---|---|
| `resume` | weiterschauen, wo du aufgehört hast — waipu merkt sich die Stelle selbst |
| `beginning` | von vorn abspielen |
| `details` | nur die Detailseite öffnen, ohne abzuspielen |

Die Aufnahme muss fertig sein oder gerade aufnehmen (`FINISHED`/`RECORDING`,
nicht `SCHEDULED`/`FAILED`). Wie weit du schon geschaut hast, steht als
`position_percentage` in der `recordings`-Liste.

## Erzeugte Entities

Die Entities verteilen sich auf drei Geräte. Die genauen Entity-IDs hängen
von deiner Einrichtung ab — die tatsächlichen unter *Entwicklerwerkzeuge →
Zustände* nachschauen. Vollständige Referenz:
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.

**waipu Wiedergabe** — die Fernsehersteuerung

- **`media_player`** — die Fernbedienungs-Karte für waipu: Ein/Aus und
  Lautstärke gehen an den Fernseher, der Zustand folgt ihm live.
  - **Medien-Browser** mit *Aufnahmen*, *Sender* und *Programm*
  - **Quellen** Live-TV, Aufnahmen und EPG springen direkt in den Bereich
    der waipu-App (Android TV)
  - **Weiter/Zurück** wechselt den Sender (Android TV)
  - Titel und Bild der laufenden Sendung
- **Sender-Auswahl-Menü** (`select`) — praktisch, wenn dein Dashboard schon
  den eigenen media_player des Fernsehers nutzt
- drei **Shortcut-Buttons** für Live-TV, EPG und Aufnahmen (Android TV)

**waipu Senderübersicht** — ein Satz pro Sender aus der Senderauswahl

- `sensor.<sender>_jetzt` / `_danach` — aktuelle/nächste Sendung mit
  EPG-Details (Beschreibung, FSK, Folge, Genre). `_danach` listet weitere
  `upcoming`-Sendungen mit `program_id` und `series_id` zum Aufnehmen.
- ein Button pro Sender, der aufnimmt, was gerade läuft (DVR-Abo)

**waipu Aufnahmen** — nur mit DVR-Abo

- **Kalender** mit jeder geplanten, laufenden und fertigen Aufnahme
- zwei **Sensoren** — Anzahl neuer bzw. aller Aufnahmen, jeweils mit einer
  `recordings`-Liste (inkl. `recording_id` und `position_percentage`)

## Services

Vollständige Referenz:
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

| Service | Zweck |
|---|---|
| `waipu.create_recording` | Aufnahme planen — ohne Angaben: was gerade auf dem eingestellten Sender läuft |
| `waipu.stop_recording` | laufende Aufnahme vorzeitig beenden (Aufgenommenes bleibt) |
| `waipu.delete_recording` | eine oder mehrere Aufnahmen löschen |
| `waipu.create_serial_recording` | alle künftigen Folgen einer Serie aufnehmen |
| `waipu.delete_serial_recording` | Serien-Aufnahme beenden, optional mit Löschen |
| `waipu.switch_channel_on_android_tv` | Sender am Android TV wechseln |
| `waipu.play_recording_on_android_tv` | Aufnahme am Android TV abspielen |
| `waipu.open_program_on_android_tv` | Detailseite einer Sendung am Android TV öffnen (oder mit `autoplay` abspielen) — ohne Angaben die laufende Sendung des eingestellten Senders |
| `waipu.launch_on_android_tv` | waipu am Android TV öffnen, optional direkt auf einem Sender |
| `waipu.launch_on_apple_tv` | waipu am Apple TV öffnen |

```yaml
service: waipu.create_recording
data:
  station_id: ard            # optional — Standard: der gerade eingestellte Sender
  program_id: "67ad0d26-…"   # optional — Standard: die laufende Sendung

service: waipu.delete_recording
data:
  recording_id: "1206434822" # einzelne ID oder Liste

service: waipu.create_serial_recording
data:
  station_id: ard
  program_id: "67ad0d26-…"   # optional — Standard: die laufende Sendung
```

## Dashboard-Beispiel

```yaml
type: vertical-stack
cards:
  - type: media-control
    entity: media_player.waipu_wiedergabe   # „Medien durchsuchen“ öffnet Aufnahmen und Sender
  - type: entities
    entities:
      - entity: sensor.ard_jetzt
      - entity: button.ard_aktuelles_programm_aufnehmen
      - entity: calendar.waipu_aufnahmen
```

Mehr Karten im **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Dashboard-Karten)**.

## Bekannte Einschränkungen

- **Apple TV: nur App-Start.** Für die waipu-tvOS-App sind keine Links
  bekannt, mit denen man einen Sender oder eine Aufnahme direkt öffnen
  könnte. Auf Android TV geht beides.
- **Keine 2FA.** waipu unterstützt aktuell nur den reinen Passwort-Login.
- **API-Änderungen.** waipu hat schon mehrfach ältere App-Versionen
  serverseitig blockiert. Liefert die Integration plötzlich nichts mehr,
  zuerst nach einem Update schauen.

## Entwicklung

```bash
pip install -r requirements_test.txt
pytest
```

Die Tests laufen in zwei Ebenen: `test_api_*.py`, `test_const.py`,
`test_deeplinks.py` und `test_program_station.py` prüfen die reine Logik
ohne Home Assistant; die übrigen nutzen den Home-Assistant-Test-Harness.

## Lizenz

GPL-3.0 (übernommen aus der Kodi-Plugin-Abstammung), siehe [LICENSE](LICENSE).
Ursprünglich basierend auf [GB-1972/ha-waipu](https://github.com/GB-1972/ha-waipu).
Das waipu.tv-Logo ist eine Marke der Exaring AG und wird nur zur
Kennzeichnung verwendet.
