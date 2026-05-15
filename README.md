# waipu.tv – Home Assistant Custom Integration

Inoffizielle Home-Assistant-Integration für [waipu.tv](https://www.waipu.tv/).
Liefert EPG-Daten und Cloud-Aufnahmesteuerung in HA und koppelt sich optional
mit einer bestehenden Apple-TV-Integration, um die Waipu-App per Knopfdruck
auf dem Apple TV zu starten.

> **Hinweis:** Diese Integration ist **nicht** von der Exaring AG / waipu.tv
> autorisiert. Sie nutzt eine reverse-engineerte API (Quelle: das Kodi-Plugin
> [flubshi/plugin.video.waipu.tv](https://github.com/flubshi/plugin.video.waipu.tv)).
> Waipu kann die API jederzeit ändern oder sperren.

## Was geht — und was nicht

| Funktion | Status |
|---|---|
| Login (Benutzername/Passwort, kein 2FA) | ✅ |
| Senderliste + Sender-Logos | ✅ |
| EPG: laufendes & nächstes Programm pro Sender als Sensor | ✅ |
| Cloud-Aufnahme planen (Button pro Sender + Service) | ✅ (Perfect / Perfect Plus / O2 TV L/XL) |
| Aufnahmen anzeigen (HA-Kalender) | ✅ |
| Aufnahmen löschen (Service) | ✅ |
| Waipu-App auf Apple TV starten | ✅ (App-Launch, kein Sender-Deep-Link — Waipu unterstützt das nicht) |
| Stream direkt in HA abspielen | ❌ — Widevine-DRM verhindert das |

## Installation

### Variante 1: HACS Custom Repository (empfohlen)

1. HACS → drei-Punkte-Menü → *Benutzerdefinierte Repositories*
2. URL deines GitHub-Forks eintragen, Kategorie *Integration*
3. *waipu.tv* installieren, Home Assistant neu starten

### Variante 2: Manuelle Installation

Den Ordner `custom_components/waipu/` in dein Home-Assistant-Config-Verzeichnis
kopieren:

```
<HA-config>/custom_components/waipu/
```

Anschließend Home Assistant neu starten.

## Einrichtung

1. *Einstellungen* → *Geräte & Dienste* → *Integration hinzufügen* → **waipu.tv**
2. waipu-E-Mail + Passwort eingeben
3. Nach erfolgreichem Setup unter *Konfigurieren* (Optionen) wählen:
   - **Sichtbare Sender** — schränkt ein, welche Sender Entities erzeugen
     (sonst können das je nach Paket 300+ werden)
   - **Apple-TV media_player** — dein bestehender Apple-TV-Eintrag, z. B.
     `media_player.wohnzimmer_apple_tv`
   - **Apple-TV remote** — die zugehörige Remote-Entity, optional für
     Tastenfolgen in eigenen Skripten
   - **Waipu-App Bundle-ID** — Vorgabe `de.exaring.waipu.tvos`.
     Falsche Bundle-ID? Mit dem pyatv-CLI auf dem HA-Host auslesen:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```

## Erzeugte Entities

Pro ausgewähltem Sender:

- `sensor.<sender>_jetzt` — Titel der laufenden Sendung als State,
  Beschreibung/Start/Stop/Genre/Episode als Attribute, Sender-Logo bzw.
  Preview-Bild als `entity_picture`.
- `sensor.<sender>_danach` — analog für die nächste Sendung
- `button.<sender>_aktuelles_programm_aufnehmen` — Cloud-Aufnahme starten
  (nur bei DVR-fähigem Abo)

Global:

- `media_player.waipu_tv_wiedergabe` — Senderliste als `source_list`,
  Auswahl → Waipu-App startet auf Apple TV
- `calendar.waipu_tv_aufnahmen` — alle geplanten/laufenden/fertigen Aufnahmen
  als HA-Kalender

## Services

```yaml
service: waipu.create_recording
data:
  channel_id: ARD          # Pflicht
  program_id: "12345678"   # optional — sonst läuft die aktuelle Sendung

service: waipu.delete_recording
data:
  recording_id: abc-123    # einzelne ID oder Liste

service: waipu.launch_on_apple_tv
# nutzt das in den Optionen konfigurierte Apple TV
```

## Dashboard-Beispiel

```yaml
type: entities
title: Waipu
entities:
  - entity: media_player.waipu_tv_wiedergabe
  - entity: sensor.ard_jetzt
    secondary_info: last-changed
  - entity: button.ard_aktuelles_programm_aufnehmen
  - entity: calendar.waipu_tv_aufnahmen
```

## Bekannte Einschränkungen

- **Kein Deep-Linking zu Sendern**: Die Waipu-tvOS-App kennt keine
  öffentlichen URL-Schemes für Senderwechsel. Der Sender muss nach
  App-Start manuell ausgewählt werden — oder per `remote.send_command`
  in einem eigenen Skript (siehe HA Apple-TV-Doku).
- **Keine 2FA**: waipu unterstützt aktuell nur Passwort-Login; sobald 2FA
  aktiviert wird, müsste der Flow nachgezogen werden.
- **API-Brüche**: Waipu hat schon mehrfach App-Versionen serverseitig
  gesperrt. Falls die Integration plötzlich nichts mehr liefert, prüfen ob
  ein Update im Repo verfügbar ist.

## Lizenz

GPL-3.0 (wegen Code-Erbe aus dem Kodi-Plugin). Siehe [LICENSE](LICENSE).
