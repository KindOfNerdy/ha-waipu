<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/KindOfNerdy/ha-waipu/main/custom_components/waipu/brand/dark_logo@2x.png">
    <img alt="waipu.tv" src="https://raw.githubusercontent.com/KindOfNerdy/ha-waipu/main/custom_components/waipu/brand/logo@2x.png" width="360">
  </picture>
</p>

<h3 align="center">Home Assistant integration for waipu.tv</h3>

<p align="center">
  EPG, cloud recordings and TV control — on Android TV straight to the channel or into the recording.
</p>

<p align="center">
  <a href="https://github.com/KindOfNerdy/ha-waipu/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/KindOfNerdy/ha-waipu?label=Release"></a>
  <img alt="Home Assistant 2025.8+" src="https://img.shields.io/badge/Home%20Assistant-2025.8%2B-41BDF5?logo=homeassistant&logoColor=white">
  <a href="https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml"><img alt="Validate" src="https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg"></a>
</p>

<p align="center">
  🇩🇪 <a href="README.md">Deutsch</a> · 📖 <a href="https://github.com/KindOfNerdy/ha-waipu/wiki">Wiki</a>
</p>

---

> **Disclaimer:** This integration is **not** affiliated with or endorsed
> by Exaring AG / waipu.tv. It uses a reverse-engineered API (originally
> mapped out by the Kodi plugin
> [flubshi/plugin.video.waipu.tv](https://github.com/flubshi/plugin.video.waipu.tv)).
> waipu may change or block the API at any time.

## Highlights

- 📺 **Switch channels directly** on Android TV — from the media browser,
  the channel picker, next/previous, or a service, even while the app is
  running
- 🎬 **Play recordings on the TV** — tap one in the media browser and pick
  up where you left off
- 🗓️ **EPG as sensors** — what's on now and next, per channel, with images
- ⏺️ **Cloud recordings** — schedule, stop, delete, record whole series —
  plus a recordings calendar
- 🎛️ **Everything from the remote card** — the Live TV, Recordings and EPG
  sources jump straight to that section of the waipu app

The 📖 **[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** has the full
entity/service reference, automation examples and ready-made dashboard
cards — this README is the quick start.

## What works — and what doesn't

| Feature | Status |
|---|---|
| Login (username/password, no 2FA) | ✅ |
| Channel list + station logos | ✅ |
| EPG: now-playing & next program per channel as a sensor | ✅ |
| Schedule a cloud recording (button per channel + service) | ✅ Perfect / Perfect Plus / O2 TV L/XL only |
| Stop an active recording early, delete recordings (service) | ✅ |
| Record/stop recording a whole series (service) | ✅ |
| List recordings (HA calendar, sensors) | ✅ |
| Switch channel on Android TV | ✅ directly via waipu link — see [Android TV channel switching](#android-tv-channel-switching) |
| Play a recording on Android TV | ✅ resume, from the start, or detail page — see [Recordings on Android TV](#recordings-on-android-tv) |
| Launch the waipu app on Apple TV | ✅ app launch only — no known channel links for tvOS |
| Play the stream directly in HA | ❌ blocked by Widevine DRM |

> Entity and device names follow your Home Assistant language: in English
> e.g. `ARD – now`, in German `ARD – jetzt`. The entity IDs in the examples
> assume a German-language Home Assistant.

## Installation

Requires Home Assistant **2025.8.0** or newer.

### Via the Marketplace / HACS (recommended)

1. Open the repository in your Home Assistant:

   [![Open the repository in the Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   <details>
   <summary>Without the button</summary>

   On Home Assistant 2026.11 or newer: *Settings* → *Marketplace* → *Add
   from link*, URL `https://github.com/KindOfNerdy/ha-waipu`, category
   *Integration*. On older versions with HACS: HACS → three-dot menu →
   *Custom repositories*, same URL and category.
   </details>

2. Install **waipu.tv**.
3. Restart Home Assistant.

### Manually

Copy the `custom_components/waipu/` folder to
`<HA-config>/custom_components/waipu/` and restart Home Assistant.

## Setup

1. Add the integration:

   [![Set up the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=waipu)

   or *Settings* → *Devices & services* → *Add integration* → **waipu.tv**.
2. Enter your waipu email and password. They're only used to log in; the
   entry is named after your plan (e.g. "Perfect Plus"), not your email.
3. **Choose your TV** — Android TV, Apple TV (app launch only) or none — and
   pick its entity on the next page:
   - **Android TV:** the `remote.*` entity from the official
     [Android TV Remote integration](https://www.home-assistant.io/integrations/androidtv_remote/)
     (see [Android TV](#android-tv))
   - **Apple TV:** the `media_player` from the Apple TV integration

Everything can be changed later under *Configure*.

### Options

*Configure* opens up to three pages: first TV, channel selection and EPG
cache, then the chosen TV's fields, and with "All channels" finally the
channel list.

| Option | Meaning |
|---|---|
| **TV** | Android TV, Apple TV or none. There's always exactly one; switching removes the previous one's settings. |
| **Channel selection** | Which channels get HA entities. `Favorites` (default) follows your waipu favorites live. With `All channels` you pick them on a separate page under **Visible channels**; the selection is kept even if you switch to `Favorites` in between. |
| **EPG cache TTL** | Default 60 minutes, 0 = off. Saves requests to waipu; "now"/"next" are always correct. Only short-notice schedule changes (e.g. sports running long) can arrive up to this much later. |
| **waipu app link** (Android TV) | Prefilled with `waipu://tv`. Opens the app without a specific channel. Only change it for other waipu variants (e.g. o2 TV). |
| **waipu app bundle id** (Apple TV) | Prefilled with `de.exaring.waipu.tvos`. Only change it for other variants; read it with `atvremote --id <AppleTV-MAC> apps`. |

## Android TV

The integration controls the TV through Home Assistant's official
[Android TV Remote integration](https://www.home-assistant.io/integrations/androidtv_remote/)
— it doesn't talk to the device itself. Requirements:

1. The waipu app is installed on the Android TV.
2. The Android TV Remote integration is set up and paired with the TV —
   giving you the `remote.*` entity you pick during setup.

The legacy ADB-based `androidtv` integration is **not** supported.

Channels and recordings are opened via the links the waipu app itself
understands — the same ones it uses for its "favorite channels" tiles on
the Android TV home screen.

## Android TV channel switching

Every way switches directly — whether the TV is off, another app is
running, or waipu is already open:

- open the **Channels** folder in the waipu media_player's **media browser**
- use the **channel picker** (`select`)
- **next/previous** on the media_player card — next/previous channel in
  your channel list, wrapping around at the end
- the service:

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # the waipu station id, e.g. from the media_player's station_id attribute
```

Switching takes a brief moment while the app loads the channel. The channel
order or view in the waipu app doesn't matter.

## Recordings on Android TV

Easiest via the **media browser**: tap "Browse media" on the media_player
card (or open *Media* in the sidebar).

- **Recordings** — every finished or ongoing recording, watched or not,
  newest first, with preview image. Tapping one plays it on the TV,
  resuming where you left off.
- **Channels** — your channel list; tapping one switches to it.

For more control there's the service:

```yaml
service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"   # from the recordings attribute of the recording sensors
  mode: resume                 # resume (default) | beginning | details
  # position: 600              # optional: from second 600 (wins over mode)
```

| `mode` | Effect |
|---|---|
| `resume` | continue where you left off — waipu remembers the spot itself |
| `beginning` | play from the start |
| `details` | just open the detail page, without playing |

The recording must be finished or currently recording (`FINISHED`/`RECORDING`,
not `SCHEDULED`/`FAILED`). How far you've watched is in the `recordings`
list as `position_percentage`.

## Generated entities

Entities land on three devices. Exact entity IDs depend on your setup —
check *Developer Tools → States* for yours. Full reference:
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.

**waipu Wiedergabe** — TV control

- **`media_player`** — the remote card for waipu: on/off and volume go to
  the TV, its state follows the TV live.
  - **media browser** with *Recordings* and *Channels*
  - **sources** Live TV, Recordings and EPG jump straight to that section
    of the waipu app (Android TV)
  - **next/previous** switches the channel (Android TV)
  - title and image of the current program
- **channel picker** (`select`) — handy if your dashboard already uses the
  TV's own media_player
- three **shortcut buttons** for Live TV, EPG and Recordings (Android TV)

**waipu Senderübersicht** — one set per channel in the channel selection

- `sensor.<station>_jetzt` / `_danach` — current/next program with EPG
  details (description, age rating, episode, genre). `_danach` lists
  further `upcoming` programs with `program_id` and `series_id` for
  recording.
- a button per channel that records what's on right now (DVR plan)

**waipu Aufnahmen** — DVR plans only

- **calendar** with every scheduled, ongoing and finished recording
- two **sensors** — count of new and of all recordings, each with a
  `recordings` list (including `recording_id` and `position_percentage`)

## Services

Full reference:
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

| Service | Purpose |
|---|---|
| `waipu.create_recording` | schedule a recording — without arguments: what's on the tuned channel right now |
| `waipu.stop_recording` | end an ongoing recording early (keeps what's recorded) |
| `waipu.delete_recording` | delete one or more recordings |
| `waipu.create_serial_recording` | record every future episode of a series |
| `waipu.delete_serial_recording` | stop a series recording, optionally deleting episodes |
| `waipu.switch_channel_on_android_tv` | switch the channel on the Android TV |
| `waipu.play_recording_on_android_tv` | play a recording on the Android TV |
| `waipu.launch_on_android_tv` | open waipu on the Android TV, optionally on a channel |
| `waipu.launch_on_apple_tv` | open waipu on the Apple TV |

```yaml
service: waipu.create_recording
data:
  station_id: ard            # optional — default: the currently tuned channel
  program_id: "67ad0d26-…"   # optional — default: the program airing now

service: waipu.delete_recording
data:
  recording_id: "1206434822" # single id or list

service: waipu.create_serial_recording
data:
  station_id: ard
  program_id: "67ad0d26-…"   # optional — default: the program airing now
```

## Dashboard example

```yaml
type: vertical-stack
cards:
  - type: media-control
    entity: media_player.waipu_wiedergabe   # "Browse media" opens recordings and channels
  - type: entities
    entities:
      - entity: sensor.ard_jetzt
      - entity: button.ard_aktuelles_programm_aufnehmen
      - entity: calendar.waipu_aufnahmen
```

More cards in the **[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Dashboard-Cards)**.

## Known limitations

- **Apple TV: app launch only.** No links are known for the waipu tvOS app
  that would open a channel or recording directly. On Android TV both work.
- **No 2FA.** waipu only supports plain password login today.
- **API changes.** waipu has blocked older app versions server-side more
  than once. If the integration suddenly returns nothing, check for an
  update first.

## Development

```bash
pip install -r requirements_test.txt
pytest
```

Tests come in two tiers: `test_api_*.py`, `test_const.py`,
`test_deeplinks.py` and `test_program_station.py` cover pure logic without
Home Assistant; the rest use the Home Assistant test harness.

## License

GPL-3.0 (inherited from the Kodi plugin lineage), see [LICENSE](LICENSE).
Originally based on [GB-1972/ha-waipu](https://github.com/GB-1972/ha-waipu).
The waipu.tv logo is a trademark of Exaring AG and is used for
identification only.
