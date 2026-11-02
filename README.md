# waipu.tv – Home Assistant Custom Integration

🇬🇧 [English](README.en.md)

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=waipu)
[![Validate](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg)](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml)

Inoffizielle Home-Assistant-Integration für [waipu.tv](https://www.waipu.tv/),
einen deutschen IPTV-Streaming-Dienst. Bringt EPG-Daten und Cloud-DVR-Steuerung
nach HA, und koppelt optional mit einer vorhandenen Apple-TV- oder
Android-TV-Integration, um die waipu-App per Knopfdruck auf dem Fernseher zu
starten — auf Android TV direkt auf dem gewünschten Sender oder mit einer
bestimmten Aufnahme.

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
| Laufende Aufnahme vorzeitig stoppen (Service) | ✅ |
| Aufnahmen auflisten (HA-Kalender) | ✅ |
| Aufnahmen löschen (Service) | ✅ |
| waipu-App auf Apple TV starten | ✅ (nur App-Start — für tvOS sind keine Sender-Links bekannt) |
| waipu-App auf Android TV starten | ✅ (optional direkt auf einem Sender) |
| Sender auf Android TV wechseln (media_player, Auswahl-Menü, Service) | ✅ direkt per waipu-Link — siehe [Android-TV-Senderwechsel](#android-tv-senderwechsel) |
| Aufnahme auf Android TV abspielen (Medien-Browser, Service) | ✅ fortsetzen, von vorn oder Detailseite — siehe [Aufnahmen auf Android TV](#aufnahmen-auf-android-tv) |
| Serien-Aufnahme starten/beenden (Service) | ✅ beide live bestätigt funktionsfähig |
| Stream direkt in HA abspielen | ❌ — durch Widevine-DRM blockiert |

> Die Namen der Entities und Geräte richten sich nach der Sprache deines Home Assistant: auf Deutsch z. B. `ARD – jetzt`, auf Englisch `ARD – now`. Die Entity-IDs in den Beispielen hier gehen von einem deutschsprachigen Home Assistant aus.

## Installation

Benötigt Home Assistant **2025.8.0** oder neuer.

### Option 1: Marketplace / HACS (empfohlen)

Ein-Klick-Installation über den ersten Badge oben in diesem README — öffnet
dieses Repository im Marketplace deiner Home-Assistant-Instanz (in HACS bei
Versionen vor 2026.11) und bietet an, es als benutzerdefiniertes Repository
hinzuzufügen.

Oder manuell, ab Home Assistant 2026.11:

1. *Einstellungen* → *Marketplace* → *Add from link* (braucht die GitHub-Verbindung des Marketplace)
2. URL: `https://github.com/KindOfNerdy/ha-waipu`, Kategorie *Integration*
3. **waipu.tv** installieren, Home Assistant neu starten

Bei älteren Versionen mit HACS: HACS → Drei-Punkte-Menü →
*Benutzerdefinierte Repositories*, gleiche URL und Kategorie.

### Option 2: Manuelle Installation

Den Ordner `custom_components/waipu/` in dein Home-Assistant-Konfigurationsverzeichnis kopieren:

```
<HA-config>/custom_components/waipu/
```

Danach Home Assistant neu starten.

## Einrichtung

1. *Einstellungen* → *Geräte & Dienste* → *Integration hinzufügen* → **waipu.tv**
   (oder über den zweiten Badge oben in diesem README)
2. waipu-E-Mail + Passwort eingeben (wird nur zum Login genutzt — erscheint
   nirgends in der UI; der Eintrag wird nach deinem Abo-Namen benannt, sobald
   der bekannt ist, z. B. "Perfect Plus", nicht nach deiner E-Mail)
3. Danach fragt der Assistent, welcher **Fernseher** gesteuert werden soll —
   **Android TV**, **Apple TV** (nur App-Start) oder **keiner** — und zeigt
   auf der nächsten Seite nur die Felder für diesen Fernseher:
   - Android TV: die **Android-TV remote-Entity** — deine vorhandene
     `remote.*`-Entity aus der offiziellen
     [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)-Integration,
     z. B. `remote.wohnzimmer_android_tv`
   - Apple TV: der **Apple-TV media_player**, z. B.
     `media_player.wohnzimmer_apple_tv`, optional die passende
     **Apple-TV remote** für eigene Tastenfolgen

   Alles hier lässt sich später noch ändern, siehe Schritt 4.
4. Nach Abschluss der Einrichtung jederzeit *Konfigurieren* (Optionen)
   öffnen. Der Dialog hat bis zu drei Seiten: zuerst Fernseher,
   Senderauswahl und EPG-Cache, dann die Felder des gewählten Fernsehers,
   bei „Alle Sender“ zuletzt die Senderliste. Die Felder im Einzelnen:
   - **Senderauswahl** — welche Sender HA-Entities bekommen (Sensoren,
     Aufnahme-Buttons, die Senderliste von media_player und Auswahl-Menü):
     - `Favoriten` (Standard) — folgt live deinen waipu-Favoriten. Was du in
       der waipu-App als Favorit markierst, taucht automatisch in HA auf.
     - `Alle Sender` — im nächsten Schritt wählst du unter **Sichtbare
       Sender** selbst aus (ein volles waipu-Paket kann 300+ Sender bedeuten —
       nur die auswählen, die dich interessieren). Die Auswahl bleibt
       gespeichert, auch wenn du zwischendurch auf `Favoriten` wechselst.
   - **waipu-App Bundle-ID** (Apple TV) — Standard `de.exaring.waipu.tvos`,
     bereits vorausgefüllt; nur für andere waipu-Varianten (z. B. o2 TV)
     ändern. Falls falsch, die echte Bundle-ID mit pyatv vom Apple TV auslesen:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```
   - **waipu-App-Link** (Android TV, vorausgefüllt) — Standard `waipu://tv` (öffnet die Live-TV-Ansicht der
     App). Wird nur genutzt, wenn die App *ohne* bestimmten Sender geöffnet
     wird — für Senderwechsel nutzt die Integration immer den passenden
     Sender-Link. Der Start per reiner Package-ID (z. B. `de.exaring.waipu`) ist seit
     einer Google-Play-Store-Änderung unzuverlässig — siehe die
     [androidtv_remote-Dokumentation](https://www.home-assistant.io/integrations/androidtv_remote/)
     — deshalb wird standardmäßig ein Link genutzt. Überschreibe das, wenn
     du lieber auf einem anderen Bereich landen willst (z. B. `waipu://epg`,
     `waipu://recordings`) oder dein Gerät einen anderen Wert braucht (z. B.
     für `o2 TV powered by waipu.tv`).
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

Anders als bei Apple TV öffnet die Integration auf Android TV direkt den
gewünschten Sender bzw. die gewünschte Aufnahme — über die Links, die die
waipu-App selbst versteht (dieselben, die sie auch für die Kacheln
„Ihre Lieblingssender“ im Android-TV-Startbildschirm nutzt).

## Android-TV-Senderwechsel

Ein Sender lässt sich auf mehreren Wegen wählen — alle schalten direkt um,
egal ob der Fernseher aus ist, gerade eine andere App läuft oder waipu schon
offen ist:

- im Medien-Browser des `media_player` den Ordner **Sender** öffnen oder das
  Sender-Auswahl-Menü nutzen
- Weiter-/Zurück-Tasten der media_player-Karte (nächster/vorheriger Sender
  aus deiner Senderliste, am Ende geht es wieder von vorn los)
- der Service:

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # die waipu-Sender-ID (steht z. B. im station_id-Attribut des media_players)
```

Das Umschalten dauert einen kleinen Moment, weil die App den Sender neu
lädt. Die Reihenfolge oder Ansicht in der waipu-App spielt keine Rolle.

## Aufnahmen auf Android TV

Am bequemsten über den **Medien-Browser**: An der media_player-Karte (oder
unter *Medien* in der Seitenleiste) auf „Medien durchsuchen“ tippen. Dort
gibt es zwei Ordner:

- **Aufnahmen** — alle fertigen und gerade laufenden Aufnahmen, egal ob
  schon gesehen oder nicht, neueste zuerst, mit Vorschaubild. Antippen
  spielt die Aufnahme am Fernseher ab und setzt dort fort, wo du aufgehört
  hast.
- **Sender** — deine Senderliste; Antippen schaltet am Fernseher um.

Für mehr Kontrolle (von vorn, nur Detailseite, bestimmte Stelle) gibt es
den Service `waipu.play_recording_on_android_tv`:

```yaml
service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"   # aus dem recordings-Attribut der Aufnahmen-Sensoren
  mode: resume                 # resume (Standard) | beginning | details
  # position: 600              # optional: ab Sekunde 600 abspielen (hat Vorrang vor mode)
```

- `resume` — weiterschauen, wo du aufgehört hast (waipu merkt sich die
  Stelle selbst)
- `beginning` — von vorn abspielen
- `details` — nur die Detailseite der Aufnahme öffnen, ohne abzuspielen

Die Aufnahme muss fertig sein oder gerade aufnehmen (`FINISHED`/`RECORDING`,
nicht `SCHEDULED`/`FAILED`). Wie weit du schon geschaut hast, steht als
`position_percentage` in der `recordings`-Liste — praktisch für eine Karte,
die „Fortsetzen“ oder „Abspielen“ anbietet.

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

- die `media_player`-Entity — mit Medien-Browser (Aufnahmen und Sender,
  siehe [Aufnahmen auf Android TV](#aufnahmen-auf-android-tv)); startet/steuert den
  konfigurierten Fernseher;
  `state`, Lautstärke und Quelle folgen live dem echten Fernseher. Auf
  Android TV springt die Quellenauswahl (**Live-TV**, **Aufnahmen**, **EPG**)
  direkt in den jeweiligen Bereich der waipu-App — so erreichst du alles von
  der Fernbedienungs-Karte aus —, und die
  Weiter-/Zurück-Tasten der Karte wechseln zum nächsten/vorherigen Sender —
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
  `recordings`-Liste als Attribut (inkl. `recording_id` und
  `position_percentage` für [Aufnahmen auf Android TV](#aufnahmen-auf-android-tv)).

## Services

Vollständige Referenz mit mehr Beispielen:
**[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

```yaml
service: waipu.create_recording
data:
  station_id: ard          # optional — Standard: der Sender, den diese
                            # Integration gerade eingestellt hat (media_player/select)
  program_id: "67ad0d26-…" # optional, UUID — Standard: aktuell laufendes Programm

service: waipu.stop_recording
data:
  recording_id: "1206434822"   # optional — Standard: laufende Aufnahme auf dem
                                # gerade eingestellten Sender. Kombiniert mit
                                # create_recording (beide weggelassen) nimmt das
                                # nur ein paar Minuten von dem auf, was gerade läuft.

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
data:
  station_id: zdf      # optional — ohne: App öffnen, mit: direkt auf diesen Sender

service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # siehe Abschnitt oben

service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"
  mode: resume          # resume | beginning | details — siehe Abschnitt oben
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

- **Apple TV: nur App-Start.** Für die waipu-tvOS-App sind keine Links
  bekannt, mit denen man einen Sender oder eine Aufnahme direkt öffnen
  könnte — dort muss der Sender nach dem Start manuell gewählt werden. Auf
  Android TV geht beides direkt.
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

## Tests ausführen

```bash
pip install -r requirements_test.txt
pytest
```

Zwei Ebenen: `test_api_*.py`/`test_const.py`/`test_program_station.py`
decken die reine Logik ab (Payload-Parsing, Slot-Mathematik, Programm-/
Sender-Auswahl, Abo-Stufen-Erkennung), komplett ohne Home Assistant.
`test_config_flow.py`/`test_setup_auth.py` prüfen den echten Config-Flow
sowie Setup-/Reauth-Verhalten über `pytest-homeassistant-custom-component`
— das zieht das komplette `homeassistant`-Paket nach, ist also der
langsame Teil von `pip install`.

## Lizenz

GPL-3.0 (übernommen aus der Kodi-Plugin-Abstammung). Siehe [LICENSE](LICENSE).

Ursprünglich basierend auf [GB-1972/ha-waipu](https://github.com/GB-1972/ha-waipu).
