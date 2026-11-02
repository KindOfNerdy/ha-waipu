# waipu.tv – Home Assistant Custom Integration

🇩🇪 [Deutsch](README.md)

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=waipu)
[![Validate](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg)](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml)

Unofficial Home Assistant integration for [waipu.tv](https://www.waipu.tv/),
a German IPTV streaming service. Surfaces EPG data and cloud-DVR control
in HA, and optionally couples with an existing Apple TV or Android TV
integration to launch the waipu app on the TV at the press of a button —
on Android TV straight onto the channel you want, or into a specific
recording.

📖 **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** — full entity/service
reference, Android TV channel-switching explained in depth, worked
automation/script examples, and ready-to-adjust dashboard cards (this
README stays a quick start).

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
| Stop an active recording early (service) | ✅ |
| List recordings (HA calendar) | ✅ |
| Delete recordings (service) | ✅ |
| Launch the waipu app on Apple TV | ✅ (app launch only — no known channel links for tvOS) |
| Launch the waipu app on Android TV | ✅ (optionally straight onto a channel) |
| Switch channel on Android TV (media_player, channel picker, service) | ✅ directly via waipu link — see [Android TV channel switching](#android-tv-channel-switching) |
| Play a recording on Android TV (service) | ✅ resume, from the start, or detail page — see [Recordings on Android TV](#recordings-on-android-tv) |
| Record/stop recording a whole series (service) | ✅ both confirmed working live |
| Play the stream directly in HA | ❌ — blocked by Widevine DRM |

> Entity and device names follow your Home Assistant language: in English e.g. `ARD – now`, in German `ARD – jetzt`. The entity IDs in the examples here assume a German-language Home Assistant.

## Installation

Requires Home Assistant **2025.8.0** or newer.

### Option 1: Marketplace / HACS (recommended)

One-click add via the first badge at the top of this README — it opens this
repository in the Marketplace on your Home Assistant instance (in HACS on
versions before 2026.11) and offers to add it as a custom repository.

Or manually, on Home Assistant 2026.11 or newer:

1. *Settings* → *Marketplace* → *Add from link* (needs the Marketplace's GitHub connection)
2. URL: `https://github.com/KindOfNerdy/ha-waipu`, category *Integration*
3. Install **waipu.tv**, restart Home Assistant

On older versions with HACS: HACS → three-dot menu → *Custom repositories*,
same URL and category.

### Option 2: Manual install

Copy the `custom_components/waipu/` folder into your Home Assistant config
directory:

```
<HA-config>/custom_components/waipu/
```

Then restart Home Assistant.

## Setup

1. *Settings* → *Devices & services* → *Add integration* → **waipu.tv**
   (or use the second badge at the top of this README)
2. Enter your waipu email + password (only used to log in — never shown
   in the UI; the entry is titled after your subscription plan once it's
   known, e.g. "Perfect Plus", not your email)
3. The setup wizard then asks, right away, whether you want to pair an
   **Apple TV** and/or **Android TV**:
   - **Apple TV media_player** — your existing Apple TV entity, e.g.
     `media_player.living_room_apple_tv`
   - **Apple TV remote** — the matching remote entity, optional for sending
     key macros from your own scripts
   - **Android TV remote entity** — your existing `remote.*` entity from
     the official [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)
     integration, e.g. `remote.living_room_android_tv`

   All three fields are optional and independent of each other — set up
   one, both, or neither, and this step can simply be skipped (submit the
   empty form). Everything here can be added or changed later too, see
   step 4.
4. After setup completes, open *Configure* (options) any time to change
   the above, or set the more advanced options:
   - **Channel selection** — which stations get HA entities (sensors,
     recording buttons, the channel list of media_player and channel picker):
     - `Favorites` (default) — follows your waipu favorites live. Whatever
       you mark as a favorite in the waipu app shows up in HA automatically.
     - `All channels` — the next step lets you pick them yourself under
       **Visible channels** (a full waipu package can mean 300+ channels —
       pick the ones you care about). The selection is kept even if you
       switch to `Favorites` in between.
   - **waipu app bundle id** — defaults to `de.exaring.waipu.tvos`. If
     wrong, read the actual bundle id from your Apple TV with pyatv on
     the HA host:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```
   - **waipu app link** — defaults to `waipu://tv` (opens the app's live-TV
     view). Only used when the app is opened *without* a specific channel —
     channel switches always use the matching channel link. Launching by bare package id (e.g. `de.exaring.waipu`) is
     unreliable on Android TV since a Google Play Store change — see the
     [androidtv_remote docs](https://www.home-assistant.io/integrations/androidtv_remote/)
     — so a link is used by default instead. Override this if you'd
     rather land on a different section (e.g. `waipu://epg`,
     `waipu://recordings`) or your device needs a different value (e.g. for
     `o2 TV powered by waipu.tv`).
   - **EPG cache TTL** — defaults to 60 minutes, 0 disables caching. Each
     fetched EPG grid slot (a 4h block) is reused for this long before
     being refetched, instead of hitting waipu's server on every 5-minute
     poll — cuts request volume substantially without making any single
     poll bigger. Doesn't affect which program shows as "now"/"next" —
     that's always computed against the real current time. The only
     tradeoff: a late schedule correction (e.g. live sports overrunning)
     can take up to this long to show up locally.

## Android TV

Launching the waipu app on Android TV relies entirely on Home Assistant's
official [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)
integration — this integration only calls into it, it does not talk to the
TV directly. Before configuring the fields above, make sure:

1. The waipu app is already installed on the Android TV (Play Store).
2. The `androidtv_remote` integration is set up in Home Assistant and paired
   with the TV, giving you a `remote.*` entity for it.

Then point **Android TV remote entity** at that `remote.*` entity. The
legacy ADB-based `androidtv` integration is **not** supported — it's
unmaintained and less reliable for this use case; use `androidtv_remote`.

Unlike Apple TV, on Android TV the integration opens the channel or
recording you want directly — via the links the waipu app itself
understands (the same ones it uses for its "favorite channels" tiles on
the Android TV home screen).

## Android TV channel switching

There are several ways to pick a channel — all of them switch directly,
whether the TV is off, another app is running, or waipu is already open:

- pick a source on the `media_player`, or use the channel picker (select)
- the media_player card's next/previous buttons (next/previous channel in
  your channel list, wrapping around at the end)
- the service:

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # the waipu station id (e.g. from the media_player's station_id attribute)
```

Switching takes a brief moment while the app loads the channel. The channel
order or view in the waipu app doesn't matter.

## Recordings on Android TV

`waipu.play_recording_on_android_tv` opens a cloud recording right on the
TV:

```yaml
service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"   # from the recordings attribute of the recording sensors
  mode: resume                 # resume (default) | beginning | details
  # position: 600              # optional: play from second 600 (wins over mode)
```

- `resume` — continue where you left off (waipu remembers the spot itself)
- `beginning` — play from the start
- `details` — just open the recording's detail page, without playing

The recording must be finished or currently recording (`FINISHED`/`RECORDING`,
not `SCHEDULED`/`FAILED`). How far you've watched is in the `recordings`
list as `position_percentage` — handy for a card offering "Resume" vs. "Play".

## Generated entities

Full attribute-level reference: see the
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.
Entities land on one of three devices; exact entity ids depend on your
setup history (renaming a device doesn't rename entity ids already
created against it), so treat the ones below as illustrative — check
*Developer Tools → States* for yours.

**waipu Senderübersicht** (one set per selected channel):

- `sensor.<station>_jetzt` / `_danach` — title of the current/next program
  as state, with EPG details (`description`, `parental_guidance`/FSK,
  `rerun`, episode/genre info) as attributes. `_danach` also lists
  further `upcoming` programs (with `program_id`, `episode_title` and
  `series_id`, usable with `waipu.create_recording`/
  `waipu.create_serial_recording` to record something later than "now").
- a button per channel — record what's on right now (DVR subscriptions
  only).

**waipu Wiedergabe** (TV control):

- the `media_player` entity — launches/controls whichever TV is
  configured (Apple TV takes precedence if both are set — use the
  dedicated services to target either explicitly); `state`, volume, and
  source follow the real TV live. On Android TV, picking a source tunes
  straight to that channel, and the card's next-track/previous-track
  buttons step to the next/previous channel — see
  [Android TV channel switching](#android-tv-channel-switching).
- a plain channel `select` dropdown, independent of the media_player —
  handy if your dashboard already uses the TV's own native media_player
  for turn on/off, volume, and other apps like Netflix.
- Three Android-TV-only shortcut buttons to jump straight to the app's
  TV/EPG/recordings views.

**waipu Aufnahmen** (recording management, DVR subscriptions only):

- the recordings `calendar` — every scheduled/ongoing/finished recording,
  with watched status and full EPG text where available.
- two sensors — unwatched / total recording counts, each with a `recordings` list
  attribute (including `recording_id` and `position_percentage` for
  [Recordings on Android TV](#recordings-on-android-tv)).

## Services

Full reference with more examples:
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

```yaml
service: waipu.create_recording
data:
  station_id: ard          # optional — defaults to the channel this integration
                            # currently has tuned (media_player/select)
  program_id: "67ad0d26-…" # optional UUID — defaults to the currently airing program

service: waipu.stop_recording
data:
  recording_id: "1206434822"   # optional — defaults to the running recording
                                # on the currently tuned channel. Combined with
                                # create_recording (both omitted), this records
                                # just a few minutes of whatever's on right now.

service: waipu.delete_recording
data:
  recording_id: "1206434822"   # single id or list

service: waipu.create_serial_recording   # confirmed working — see the wiki
data:
  station_id: ard
  program_id: "67ad0d26-…"   # optional — defaults to the currently airing program

service: waipu.delete_serial_recording   # confirmed working — see the wiki
data:
  series_id: "104121"   # from a sensor's series_id attribute

service: waipu.launch_on_apple_tv
# uses the Apple TV configured in the integration options

service: waipu.launch_on_android_tv
data:
  station_id: zdf      # optional — without: open the app, with: straight onto this channel

service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # see the section above

service: waipu.play_recording_on_android_tv
data:
  recording_id: "2115976245"
  mode: resume          # resume | beginning | details — see the section above
```

## Dashboard example

Adjust the entity ids below to your own (see the note in *Generated entities*):

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

## Known limitations

- **Apple TV: app launch only.** No links are known for the waipu tvOS app
  that would open a channel or recording directly — there the channel has
  to be picked manually after launch. On Android TV both work directly.
- **No 2FA.** waipu only supports plain password login today; if 2FA is
  ever enabled on your account, the flow here will need to be reworked.
- **API breakage.** waipu has blocked older app versions server-side
  more than once. If the integration suddenly returns nothing, check
  for an update in this repo.
- **Serial recording was reverse-engineered, now confirmed working.**
  `waipu.create_serial_recording` and `waipu.delete_serial_recording` were
  both built entirely from request shapes observed in waipu's web client,
  without ever seeing a real response — both have since been confirmed
  working live: `create_serial_recording` made the waipu app immediately
  show the series' recordings as running, and `delete_serial_recording`
  (including the "also delete already-downloaded episodes" toggle)
  correctly stopped and removed them again.

## Running the tests

```bash
pip install -r requirements_test.txt
pytest
```

Two tiers: `test_api_*.py`/`test_const.py`/`test_program_station.py` cover
the pure logic (payload parsing, slot math, program/station selection,
subscription-tier detection) with no Home Assistant needed at all.
`test_config_flow.py`/`test_setup_auth.py` exercise the actual config
flow and setup/reauth behavior via `pytest-homeassistant-custom-component`
— that one pulls in the full `homeassistant` package, so it's the slow
part of `pip install`.

## License

GPL-3.0 (inherited from the Kodi plugin lineage). See [LICENSE](LICENSE).

Originally based on [GB-1972/ha-waipu](https://github.com/GB-1972/ha-waipu).
