# waipu.tv – Home Assistant Custom Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=GB-1972&repository=ha-waipu&category=integration)
[![Validate](https://github.com/GB-1972/ha-waipu/actions/workflows/validate.yml/badge.svg)](https://github.com/GB-1972/ha-waipu/actions/workflows/validate.yml)

Unofficial Home Assistant integration for [waipu.tv](https://www.waipu.tv/),
a German IPTV streaming service. Surfaces EPG data and cloud-DVR control
in HA, and optionally couples with an existing Apple TV integration to
launch the waipu app on the TV at the press of a button.

> **Disclaimer:** This integration is **not** affiliated with or endorsed
> by Exaring AG / waipu.tv. It uses a reverse-engineered API (originally
> mapped out by the Kodi plugin
> [flubshi/plugin.video.waipu.tv](https://github.com/flubshi/plugin.video.waipu.tv)).
> waipu may change or block the API at any time.

## What works — and what doesn't

| Feature | Status |
|---|---|
| Login (username/password, no 2FA) | ✅ |
| Channel list + station logos | ✅ |
| EPG: now-playing & next program per channel as a sensor | ✅ |
| Schedule a cloud recording (button per channel + service) | ✅ (Perfect / Perfect Plus / O2 TV L/XL only) |
| List recordings (HA calendar) | ✅ |
| Delete recordings (service) | ✅ |
| Launch the waipu app on Apple TV | ✅ (app launch only — waipu has no channel deep links) |
| Play the stream directly in HA | ❌ — blocked by Widevine DRM |

> The integration's entity *labels* are currently in German (`jetzt`, `danach`, `aufnahmen`, `wiedergabe`, …). The codebase otherwise speaks English; localisation can be reworked later if there's demand.

## Installation

### Option 1: HACS Custom Repository (recommended)

One-click add via the badge at the top of this README — it opens HACS on
your Home Assistant instance and registers this repository directly.

Or manually:

1. HACS → three-dot menu → *Custom repositories*
2. URL: `https://github.com/GB-1972/ha-waipu`, category *Integration*
3. Install **waipu.tv**, restart Home Assistant

### Option 2: Manual install

Copy the `custom_components/waipu/` folder into your Home Assistant config
directory:

```
<HA-config>/custom_components/waipu/
```

Then restart Home Assistant.

## Setup

1. *Settings* → *Devices & services* → *Add integration* → **waipu.tv**
2. Enter your waipu email + password
3. After a successful setup, open *Configure* (options) and choose:
   - **Visible channels** — limits which stations get HA entities (a
     full waipu package can mean 300+ channels — pick the ones you care about)
   - **Apple TV media_player** — your existing Apple TV entity, e.g.
     `media_player.living_room_apple_tv`
   - **Apple TV remote** — the matching remote entity, optional for sending
     key macros from your own scripts
   - **waipu app bundle id** — defaults to `de.exaring.waipu.tvos`. If
     wrong, read the actual bundle id from your Apple TV with pyatv on
     the HA host:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```

## Generated entities

Per selected channel:

- `sensor.<station>_jetzt` — title of the currently airing program as
  state, with description / start / stop / genre / episode info as
  attributes; station logo or preview image as `entity_picture`.
- `sensor.<station>_danach` — same shape, but for the next program.
- `button.<station>_aktuelles_programm_aufnehmen` — schedule a cloud
  recording of whatever is on right now (only created for DVR-enabled
  subscriptions).

Global:

- `media_player.waipu_tv_wiedergabe` — channel list as `source_list`;
  selecting a source launches the waipu app on the configured Apple TV.
- `calendar.waipu_tv_aufnahmen` — every scheduled / ongoing / finished
  cloud recording as a HA calendar.

## Services

```yaml
service: waipu.create_recording
data:
  station_id: ard          # required (lower-case waipu station id)
  program_id: "67ad0d26-…" # optional UUID — defaults to the currently airing program

service: waipu.delete_recording
data:
  recording_id: "1206434822"   # single id or list

service: waipu.launch_on_apple_tv
# uses the Apple TV configured in the integration options
```

## Dashboard example

```yaml
type: entities
title: waipu
entities:
  - entity: media_player.waipu_tv_wiedergabe
  - entity: sensor.ard_jetzt
    secondary_info: last-changed
  - entity: button.ard_aktuelles_programm_aufnehmen
  - entity: calendar.waipu_tv_aufnahmen
```

## Known limitations

- **No per-channel deep linking.** The waipu tvOS app exposes no public
  URL schemes for channel switching. After app launch the channel must
  be picked manually — or via `remote.send_command` in your own script
  (see the Home Assistant Apple TV docs).
- **No 2FA.** waipu only supports plain password login today; if 2FA is
  ever enabled on your account, the flow here will need to be reworked.
- **API breakage.** waipu has blocked older app versions server-side
  more than once. If the integration suddenly returns nothing, check
  for an update in this repo.

## License

GPL-3.0 (inherited from the Kodi plugin lineage). See [LICENSE](LICENSE).
