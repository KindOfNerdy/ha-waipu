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

- 📺 **Sender direkt umschalten** auf Android TV — aus dem Medien-Browser, der
  Senderauswahl der waipu-Karte, mit Weiter/Zurück oder per Automation, auch
  bei laufender App
- 🎬 **Aufnahmen am Fernseher abspielen** — im Medien-Browser antippen und
  weiterschauen, wo du aufgehört hast
- 🗓️ **EPG als Sensoren** — was läuft jetzt und danach, pro Sender, mit Bild
- ⏺️ **Cloud-Aufnahmen** planen, stoppen, löschen, ganze Serien aufnehmen —
  plus Aufnahmen-Kalender
- 🎛️ **Alles von der Fernbedienungs-Karte** — Quellen Live-TV, Aufnahmen,
  EPG und Mediathek springen direkt in den jeweiligen Bereich der waipu-App
- 👀 **Weiß, was am Fernseher läuft** — auch wenn du am TV selbst umschaltest,
  eine Aufnahme oder einen Film aus der waiputhek schaust (über Google Cast)
- ⏯️ **Pause, Springen, von vorn** — direkt aus der Karte; „Sendung von vorn“
  startet die laufende Live-Sendung neu
- 🔔 **Erinnern und umschalten** — ein Push ein paar Minuten vorher, zu
  Beginn schaltet der Fernseher um; für eine Sendung, eine Serie oder nach
  Zeitplan
- 🖼️ **Eigene Dashboard-Karten inklusive** — Player, „Jetzt im TV“,
  Aufnahmen, Programm-Raster und Erinnerungen, ohne zusätzliche Installation

Das 📖 **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** hat die
vollständige Entity-/Service-Referenz, Automations-Beispiele und fertige
Dashboard-Karten — dieses README ist der Schnelleinstieg.

## Was funktioniert — und was nicht

| Funktion | Status |
|---|---|
| Login (Benutzername/Passwort, keine 2FA) | ✅ |
| Senderliste + Sender-Logos | ✅ |
| EPG: laufendes & nächstes Programm pro Sender als Sensor | ✅ |
| Cloud-Aufnahme planen (Medien-Browser, Service, optional Button pro Sender) | ✅ nur Perfect / Perfect Plus / O2 TV L/XL |
| Laufende Aufnahme vorzeitig stoppen, Aufnahmen löschen (Service) | ✅ |
| Serien-Aufnahme starten/beenden (Service) | ✅ |
| Aufnahmen auflisten (HA-Kalender, Sensoren) | ✅ |
| Sender auf Android TV wechseln | ✅ direkt per waipu-Link — siehe [Android-TV-Senderwechsel](#android-tv-senderwechsel) |
| Aufnahme auf Android TV abspielen | ✅ fortsetzen, von vorn oder Detailseite — siehe [Aufnahmen auf Android TV](#aufnahmen-auf-android-tv) |
| Erkennen, was am TV läuft (Sender, Aufnahme, waiputhek) | ✅ mit Google-Cast-Entität — siehe [Was am Fernseher läuft](#was-am-fernseher-läuft-google-cast) |
| Pause/Play, Springen, Sendung von vorn | ✅ Android TV; Springen in der waiputhek nur mit Google-Cast-Entität |
| waipu-App auf Apple TV starten | ✅ nur App-Start — für tvOS sind keine Sender-Links bekannt |
| Stream direkt in HA abspielen | ❌ durch Widevine-DRM blockiert |

> Die Namen der Entities und Geräte richten sich nach der Sprache deines Home
> Assistant: auf Deutsch z. B. `ARD – jetzt`, auf Englisch `ARD – now`. Die
> Entity-IDs in den Beispielen gehen von einem deutschsprachigen Home
> Assistant aus.

## Installation

Benötigt Home Assistant **2025.8.0** oder neuer.

### Über den Marketplace / HACS (empfohlen)

1. Repository hinzufügen (*Add from link*, URL `https://github.com/KindOfNerdy/ha-waipu`, Kategorie *Integration*):

   [![Repositories im Marketplace öffnen](https://my.home-assistant.io/badges/marketplace_repositories.svg)](https://my.home-assistant.io/redirect/marketplace_repositories/)

2. Repository in deinem Home Assistant öffnen:

   [![Repository im Marketplace öffnen](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   Bei älteren Versionen mit HACS:

   [![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   <details>
   <summary>Ohne Button</summary>

   Ab Home Assistant 2026.11: *Einstellungen* → *Marketplace* → *Add from
   link*, URL `https://github.com/KindOfNerdy/ha-waipu`, Kategorie
   *Integration*. Bei älteren Versionen mit HACS: HACS → Drei-Punkte-Menü →
   *Benutzerdefinierte Repositories*, gleiche URL und Kategorie.
   </details>

3. **waipu.tv** installieren.
4. Home Assistant neu starten.

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
   deiner E-Mail. Im waipu-Konto erscheint die Anmeldung unter *Geräte* als
   „Home Assistant (ha-waipu …)“. waipu hält höchstens fünf Anmeldungen;
   eine neue verdrängt die älteste. Trifft es Home Assistant, meldet sich
   die Integration mit dem gespeicherten Passwort selbst wieder an — und
   verdrängt dabei ihrerseits das älteste Gerät. Nicht mehr genutzte
   Einträge dort also besser entfernen.
3. **Fernseher wählen** — Android TV, Apple TV (nur App-Start) oder keiner —
   und auf der nächsten Seite dessen Entity auswählen:
   - **Android TV:** die `remote.*`-Entity aus der offiziellen
     [Android-TV-Remote-Integration](https://www.home-assistant.io/integrations/androidtv_remote/)
     (siehe [Android TV](#android-tv))
   - **Apple TV:** der `media_player` aus der Apple-TV-Integration

Alles lässt sich später unter *Konfigurieren* ändern.

### Optionen

*Konfigurieren* öffnet bis zu drei Seiten: zuerst Fernseher und
Senderauswahl, dann die Felder des gewählten Fernsehers, bei „Alle Sender“
zuletzt die Senderliste.

| Option | Bedeutung |
|---|---|
| **Fernseher** | Android TV, Apple TV oder keiner. Es gibt immer genau einen; ein Wechsel entfernt die Einstellungen des bisherigen. |
| **Senderauswahl** | Welche Sender HA-Entities bekommen. `Favoriten` (Standard) folgt live deinen waipu-Favoriten. Bei `Alle Sender` wählst du auf einer eigenen Seite unter **Sichtbare Sender** aus; die Auswahl bleibt gespeichert, auch wenn du zwischendurch auf `Favoriten` wechselst. |
| **Google-Cast-Entität** (Android TV, optional) | Der `media_player` des Fernsehers aus der [Google-Cast-Integration](https://www.home-assistant.io/integrations/cast/). Damit erkennt die Integration, was am TV läuft, und kann in der waiputhek springen — siehe [Was am Fernseher läuft](#was-am-fernseher-läuft-google-cast). |
| **waipu-App-Link** (Android TV) | Vorausgefüllt mit `waipu://tv`. Öffnet die App ohne bestimmten Sender. Nur für andere waipu-Varianten (z. B. o2 TV) ändern. |
| **waipu-App Bundle-ID** (Apple TV) | Vorausgefüllt mit `de.exaring.waipu.tvos`. Nur für andere Varianten ändern; auslesen mit `atvremote --id <AppleTV-MAC> apps`. |
| **Erinnerungen per Push an** | Ein oder mehrere Benachrichtigungsziele, z. B. die Companion-App auf dem Handy. Leer = kein Push; umgeschaltet wird trotzdem. Siehe [Erinnern und umschalten](#erinnern-und-umschalten). |
| **Erinnern so viele Minuten vorher** | Standard 5. Bei 0 kommt der Push erst zu Beginn. |

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
- **Weiter/Zurück** an der media_player-Karte — nächster/vorheriger Sender
  aus deiner Senderliste, am Ende geht es wieder von vorn los
- in Automationen und Skripten `media_player.play_media` mit der
  waipu-Sender-ID:

```yaml
action: media_player.play_media
target:
  entity_id: media_player.waipu_wiedergabe
data:
  media_content_type: channel
  media_content_id: swr_bw   # die waipu-Sender-ID, z. B. aus dem station_id-Attribut des media_players
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
  Sendungen sind mit „⏺ geplant“ markiert und bieten **Aufnahme abbrechen**
  an; läuft für die Serie schon eine Serien-Aufnahme, steht statt „Serie
  aufnehmen“ **Serien-Aufnahme beenden** da (bereits Aufgenommenes bleibt). Ist Aufnehmen nicht erlaubt (Abo, Sender oder Sendung), öffnet eine
  kommende Sendung direkt ihre Detailseite. Die laufende Sendung von vorn
  startest du mit `waipu.restart_program` (siehe
  [Was am Fernseher läuft](#was-am-fernseher-läuft-google-cast)).

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

## Was am Fernseher läuft (Google Cast)

Die Android-TV-Remote-Integration verrät nur, *welche App* vorn ist, nicht
den Sender. Die [Google-Cast-Integration](https://www.home-assistant.io/integrations/cast/)
legt für viele Android-Fernseher aber automatisch einen `media_player` an,
der meldet, was die waipu-App gerade abspielt. Er heißt meist wie dein
Fernseher; den richtigen erkennst du daran, dass er bei laufender waipu-App
`waipu.tv` als App anzeigt. Wählst du ihn unter *Konfigurieren → Android
TV* als **Google-Cast-Entität** aus, zeigt die waipu-Karte immer, was
wirklich läuft:

| Am Fernseher läuft | Quelle in der Karte | Anzeige |
|---|---|---|
| Live-TV | Live-TV | Sender und laufende Sendung — auch wenn du am TV selbst umgeschaltet hast |
| Live mit Pause oder Restart | Live-TV | die Sendung, die du gerade siehst, und wie viele Minuten du hinter Live bist (`timeshift_minutes`) |
| eine Aufnahme | Aufnahmen | Titel, Sender, von dem sie stammt, Fortschrittsbalken |
| ein Film aus der waiputhek | Mediathek | Titel, Bild, Fortschrittsbalken |

Damit lässt sich auch steuern:

- **Pause/Play** an der Karte (ohne Cast-Entität über die Pause-Taste der
  Fernbedienung). Bei Sendungen, die waipu nicht pausieren lässt, fehlt
  der Knopf.
- **Springen** im Fortschrittsbalken bei Aufnahmen und waiputhek. Springst
  du über einen Werbeblock, zeigt waipu erst die Werbung und springt dann
  selbst an die gewählte Stelle. Aufnahmen gehen auch ohne Cast-Entität —
  waipu lädt dann kurz neu. Auch live lässt sich innerhalb der laufenden
  Sendung springen (`media_player.media_seek` mit einer Unix-Zeit, z. B. über
  die ±30-s-Knöpfe der waipu-Karte) — das geht ohne Cast-Entität.
- **Sendung von vorn** mit `waipu.restart_program` — das geht auch ohne
  Cast-Entität. Das Attribut `restart_available` sagt, ob das bei der
  laufenden Sendung erlaubt ist — manche Sender (z. B. ProSieben, SAT.1)
  lassen live nicht spulen.

Weiter/Zurück an der Karte wechselt weiterhin den Sender.

## Erzeugte Entities

Die Entities verteilen sich auf drei Geräte. Die genauen Entity-IDs hängen
von deiner Einrichtung ab — die tatsächlichen unter *Entwicklerwerkzeuge →
Zustände* nachschauen. Vollständige Referenz:
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.

**waipu Wiedergabe** — die Fernsehersteuerung

- **`media_player`** — die Fernbedienungs-Karte für waipu: Ein/Aus und
  Lautstärke gehen an den Fernseher, der Zustand folgt ihm live.
  - **Medien-Browser** mit *Aufnahmen*, *Sender* und *Programm*
  - **Quellen** Live-TV, Aufnahmen, EPG und Mediathek springen direkt in
    den Bereich der waipu-App; EPG öffnet beim gerade eingestellten Sender
    (Android TV)
  - **Weiter/Zurück** wechselt den Sender (Android TV)
  - Titel und Bild von dem, was läuft — mit Google-Cast-Entität auch
    Aufnahmen und waiputhek, mit Pause, Fortschrittsbalken und Springen
  - Attribut `channels` — deine Senderliste, z. B. für eine Senderauswahl
    in eigenen Dashboard-Karten
- vier **Shortcut-Buttons** für Live-TV, EPG, Aufnahmen und Mediathek — wie
  die Quellen (Android TV)
- **Erinnerungen** — wann die nächste startet; im Attribut `reminders` alle
  Erinnerungen, in `upcoming` die nächsten Termine

**waipu Senderübersicht** — ein Satz pro Sender aus der Senderauswahl

- `sensor.<sender>_jetzt` / `_danach` — aktuelle/nächste Sendung mit
  EPG-Details (Beschreibung, FSK, Folge, Genre). `_danach` listet weitere
  `upcoming`-Sendungen mit `program_id` und `series_id` zum Aufnehmen.
- ein Button pro Sender, der aufnimmt, was gerade läuft (DVR-Abo)

Der Aufnahme-Button ist zunächst deaktiviert — aufnehmen geht auch über den
Medien-Browser oder `waipu.create_recording`. Bei Bedarf unter
*Einstellungen → Geräte & Dienste → waipu.tv → Entities* einschalten.

**waipu Aufnahmen** — nur mit DVR-Abo

- **Kalender** mit jeder geplanten, laufenden und fertigen Aufnahme
- zwei **Sensoren** — Anzahl neuer bzw. aller Aufnahmen, jeweils mit einer
  `recordings`-Liste (inkl. `recording_id`, Sender, `position_percentage` und Bild)
- **Aufnahme-Speicher frei** — wie viele Stunden noch aufgenommen werden
  können, wie in der App; dazu belegte Stunden und Anzahl der Aufnahmen

## Erinnern und umschalten

Ein paar Minuten bevor etwas anfängt, kommt ein Push aufs Handy; zu Beginn
schaltet der Fernseher auf den Sender. Möglich ist das

- für **eine Sendung** — im Programm-Raster antippen, *Erinnern*
- für **jede Folge einer Serie** — *Serie erinnern*
- nach **Zeitplan** — Uhrzeit, Wochentage und Sender, jede Woche oder nur
  einmal; in der Karte *waipu.tv Erinnerungen* unter *Zeitplan anlegen*

Pro Erinnerung lässt sich *Zu Beginn umschalten* ausschalten, dann kommt nur
der Push. Im Push stehen *Nicht umschalten* (nur dieses Mal) und *Nicht mehr
erinnern*. Wohin der Push geht, stellst du in den
[Optionen](#optionen) ein. Für eigene Automationen gibt es das Ereignis
`waipu_reminder` (`phase`: `upcoming` vor dem Start, `start` zu Beginn).

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
| `waipu.play_recording_on_android_tv` | Aufnahme am Android TV abspielen |
| `waipu.restart_program` | laufende Live-Sendung am Android TV von vorn starten |
| `waipu.open_program_on_android_tv` | Detailseite einer Sendung am Android TV öffnen (oder mit `autoplay` abspielen) — ohne Angaben die laufende Sendung des eingestellten Senders |
| `waipu.add_reminder` | erinnern und zu Beginn umschalten — für eine Sendung, eine Serie oder nach Zeitplan |
| `waipu.update_reminder` | Erinnerung an/aus, Umschalten an/aus oder das nächste Mal auslassen |
| `waipu.remove_reminder` | Erinnerung löschen |

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

service: waipu.add_reminder
data:
  station_id: zdf
  time: "19:00"
  days: [mon, tue, wed, thu, fri]   # leer = jeden Tag
  switch: true                      # false = nur erinnern
```

## Dashboard-Karten

Die Integration bringt fünf Karten mit. Sie sind nach der Installation sofort
im Kartenauswahl-Dialog, ohne eigene Ressource; Farben und Schrift kommen aus
deinem Theme. Alle finden den waipu-Player selbst — `entity` brauchst du nur,
wenn es mehrere gibt.

### waipu.tv Player

- Bild, Titel, Sender und Folge von dem, was läuft — mit *Live*,
  *Aufnahme* oder *Mediathek*, wie weit du hinter Live bist und ob gerade
  aufgenommen wird
- Fortschritt: live die Sendezeit, bei Aufnahmen und Mediathek die Position
- Knöpfe für Sender zurück/vor, Pause/Play, 30 Sekunden zurück/vor (auch
  live), „Von vorn“ und Aufnehmen/Stoppen — nur die, die gerade gehen
- Senderauswahl mit Senderlogo und Ein/Aus

```yaml
type: custom:waipu-card
```

Unter einer Fernbedienung oder in einem Pop-up passt `mode: compact` — kleines
Bild, was läuft und die Senderauswahl. `mode: row` ist eine einzelne Zeile wie
eine Kachel, z. B. für eine „Läuft gerade“-Liste: Bild, was läuft, wie lange
noch und ein Knopf (Pause/Play, sonst Ein/Aus); Antippen öffnet die Details.

```yaml
type: custom:waipu-card
mode: compact
hide: [off_hint]   # ohne „Fernseher ist aus“: bei ausgeschaltetem TV nur die Senderauswahl
```

| Option | Bedeutung |
|---|---|
| `mode` | `full` (Standard), `compact` oder `row` |
| `hide` | Teile ausblenden: `picture`, `progress`, `controls`, `record`, `channels`, `off_hint`. Kompakt blendet `controls` aus, solange du `hide` nicht selbst setzt. |
| `tap_action` | bei `row`: was Antippen tut (Standard: Details öffnen) |

### waipu.tv Jetzt im TV

Jeder Sender mit der laufenden Sendung, Fortschritt und was danach kommt.
Antippen schaltet um (Abspiel-Zeichen am Logo); läuft eine Aufnahme, steht
daneben Stoppen. Aufgeklappt: die Beschreibung, „Aufnehmen“, „Danach
aufnehmen“, „Serie aufnehmen“, „Danach erinnern“ und „Details am TV“.

```yaml
type: custom:waipu-channels-card
channels: [ard, zdf]   # optional: nur diese Sender
```

### waipu.tv Aufnahmen

Deine Cloud-Aufnahmen mit Bild und Fortschritt, in den Reitern *Neu*,
*Verfügbar* und *Geplant*. Antippen spielt am Fernseher ab; Löschen bzw.
Abbrechen fragt einmal nach, laufende Aufnahmen lassen sich stoppen.

```yaml
type: custom:waipu-recordings-card
tab: available   # optional: new, available oder planned
max: 20          # optional: höchstens so viele Einträge
```

### waipu.tv Programm

Das Programm der nächsten sechs Stunden als Zeitleiste mit Jetzt-Linie.
Eine Sendung antippen: ansehen (läuft sie gerade), Details am TV, aufnehmen,
Serie aufnehmen, eine geplante Aufnahme abbrechen oder erinnern. Sendungen
mit Erinnerung tragen eine Glocke.

```yaml
type: custom:waipu-guide-card
channels: [ard, zdf]   # optional
```

### waipu.tv Erinnerungen

Alle Erinnerungen mit dem nächsten Termin: links groß die Uhrzeit und wann
(„heute“, „morgen“), daneben etwa „Schaltet auf ZDF“. Der Schalter macht eine Erinnerung an oder aus; aufgeklappt:
*Zu Beginn umschalten*, *Nächstes Mal auslassen* und *Löschen*. Unten legst
du einen Zeitplan an.

```yaml
type: custom:waipu-reminders-card
```

„Details am TV“ und „Von vorn“ brauchen ein angebundenes Android TV.

Nur die Senderauswahl, als Zeile in einer Entities-Karte:
`- type: custom:waipu-channel-row`. Pause, Springen und die Anzeige von
Aufnahmen und Mediathek brauchen die Google-Cast-Entität.
Karten nur aus Bordmitteln stehen im
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Dashboard-Karten)**.

## Bekannte Einschränkungen

- **Apple TV: nur App-Start.** Für die waipu-tvOS-App sind keine Links
  bekannt, mit denen man einen Sender oder eine Aufnahme direkt öffnen
  könnte. Auf Android TV geht beides.
- **Werbung ist nicht erkennbar.** Google Cast meldet während der Werbung
  dieselbe Sendung, der Fortschrittsbalken läuft einfach weiter.
- **Einzelne waiputhek-Filme lassen sich nicht aus HA starten.** Die
  Mediathek selbst öffnet sich, ein bestimmter Film braucht aber IDs, die
  die Integration nicht kennt.
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
Kennzeichnung verwendet. Die Symbole im Medien-Browser stammen aus
[Material Design Icons](https://pictogrammers.com/library/mdi/) (Apache-2.0).
