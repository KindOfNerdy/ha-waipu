# waipu.tv Android 2026.21.0 – gefundene Endpunkte (statische Analyse)

Entwickler-Notiz, keine Nutzer-Doku. Quelle: `de.exaring.waipu_2026.21.0-11203996_...apkm` (APKMirror) → `base.apk` (universal, Android 7.0+), dekompiliert mit jadx 1.5.6 am 08.11.2026. Die APK selbst liegt nicht im Repo.
Die Annotationen der Retrofit-artigen Interfaces sind obfuskiert (z. B. `@pl4` für den Pfad, `@j85` für Header). Die HTTP-Methode ist daher nicht direkt lesbar und muss bei Bedarf geprüft werden.

## Basis-Domains (Environment-Enum `noc`)

| Umgebung | Domain | Image-Host |
|---|---|---|
| PROD | `waipu.tv` | `images.wpstr.tv` |
| PREVIEW | `waipu-preview.net` | `images-preview.wpstr.tv` |
| DEV | `waipu-dev.net` | `images-dev.wpstr.tv` |

Im Code steht `{host}` als Platzhalter, z. B. `https://waiputhek.{host}/...`. Für PROD ergibt das `https://waiputhek.waipu.tv/...`.

## Subdomains mit Platzhalter `{host}`

- `waiputhek.{host}`: Startseite, Highlights, Tuner-Microsites, Content
  - `/api/pages/highlights?scope=homescreen`
  - `/api/v1/tuner/microsites/{channelId}/contents`
  - `/api/v1/tuner/contents/{contentId}`
- `stream-position.{host}`: `/api/stream-positions/{streamId}`
- `content-discovery.{host}`: `/api/recording-recommendations/most-popular`, `/api/recommendations/vod/{contentId}/next-episode`, `/api/homescreen/recently-watched/{contentId}`
- `user-stations.{host}`: `/api/stations`, `/api/stations?omitted=false`, `/api/stations/user-settings`, `/api/stations/user-settings/{stationId}`, `/api/stations/user-settings/reset`
- `web-proxy.{host}`: `/v2/station-config`
- `epg-cache.{host}`: `/api/grid/{station}/{date}`
- `permission-management.{host}`: `/api/identities/{userHandle}/permissionInstance`
- `device-api.{host}`: `/api/device-activations`
- `activation.{host}`: `/api/activation-mail`, `/api/request-reset-password`
- `customer-self-care.{host}`: `/api/doi-confirmation-email`
- `fu.{host}`: `/customer-events-forwarder/customer-events`
- `{host}` direkt: `/api/thumbnails/{channelId}/{programId}.jpg`
- Weitere Hosts (ohne Platzhalter im Fundstring): `auth.`, `app.`

## Pfade ohne Host im Code (vermutlich über Basis-URL der Umgebung)

Recording: `api/recordings`, `api/recordings/{recordingId}`, `api/recordings/{recordingId}/stop`, `api/recordings/{recordingId}/streamingdetails`, `api/recordings/summary`, `api/serials`, `api/serials/{recordingGroupId}`, `api/delete-requests`

Streams: `api/stream-url`, `api/subkey`, `api/sessions`

EPG/Programm: `api/programs/{id}`, `api/grid/{stationId}/{time}`, `api/master-data`, `api/filter`

Suche und Startseite: `api/search`, `api/suggest`, `api/v1/search`, `api/homescreen`, `api/v2/homescreen`, `api/v1/homescreen`, `api/v1/launcher`, `api/v2/launcher`, `api/v2/pages/highlights`, `api/v3/pages/highlights`

Kategorien und Empfehlungen: `api/category/{categoryId}`, `api/category/{categoryId}/all`, `api/v1/category/{categoryId}`, `api/v1/category/{categoryId}/all`, `api/recommendations/{contentArea}/{contentId}`, `api/v2/recommendations/{contentArea}/{contentId}`, `api/recommendations/vod/{contentId}/next-episode`, `api/v2/recommendations/series/{seriesId}`, `api/homescreen/recently-watched/{contentId}`

Watchlist: `api/watchlist/v1/contents`, `api/watchlist/v1/contents/ids`, `api/watchlist/v1/content/{contentId}`, `api/watchlist/v2/all`, `api/watchlist/v2/series/{seriesId}`

Media-Library: `api/media-libraries`

Nutzer und Einstellungen: `api/user-settings`, `api/user-reference-token`, `api/amazon-token`, `api/amazon-customers`, `api/device-capabilities`, `api/version-info/deprecation`

Verifikation: `api/verification`, `api/verification/pin/verify`

Home-Zones: `api/home-zones/`, `api/home-zones/validation`

Telemetrie: `WuxApiRequestDto` (Session, Event, Error, Metadata), Tabellen `wux_events`, `wux_sessions`, `wux_errors`, `wux_state_changes`

Content-Type-Beispiele: `application/vnd.waipu.waiputhek-page-v1+json`, `application/vnd.waipu.content-discovery-recommendations-v1+json`, `application/vnd.waipu.user-settings-entry-v1+json`, `application/vnd.waipu.stream-position-request.v1+json`, `application/vnd.waipu.recording-scheduler-serials-v1+json`, `application/vnd.waipu.home-zone-v1+json`

Web-Pfade (Hilfe, Jugendschutz): `waipu.tv/jugendschutz`, `https://www.waipu.tv/hilfe/articles/360000466518`, `/hilfe/tickets/new`

## Seither live bestätigt (09.11.2026)

- `epg-cache.waipu.tv/api/programs/{id}` liefert unter `restrictions` die Rechte pro Sendung (`pauseForbidden`, `seekingForbidden`, `instantRestartForbidden`, `recordingForbidden`). Anders als die Sender-Flags aus `station-config` passen sie zum eigenen Paket — genutzt in `api._program_detail_from_dict`.
- Deep-Links der Android-TV-App (`waipu://tv?id=`, `waipu://recordings?recordingId=…`, `waipu://epgdetails?…`): siehe Kommentar in `custom_components/waipu/const.py`. `waipu://waiputhek` steht im App-Manifest, ist aber ungetestet.
- Was die Google-Cast-Entität des Fernsehers über waipu meldet und wie sich Pause/Seek/Restart verhalten: siehe Kommentar in `custom_components/waipu/api.py` (Abschnitt „What waipu plays“).

## Nicht ausgewertet

- Auth-Flow (OAuth/OpenID-Login, Amazon-Login, Token-Handling)
- Welche HTTP-Methode zu welchem Pfad gehört (Annotationen obfuskiert)
- Request- und Response-Bodies (DTO-Klassen `waipux.domain.*.api.*Dto` vorhanden)
- Laufzeit-Verifikation (Traffic-Mitschnitt)
