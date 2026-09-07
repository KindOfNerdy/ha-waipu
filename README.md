# waipu.tv – Home Assistant Custom Integration

🇩🇪 [Deutsch](README.de.md)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)
[![Validate](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml/badge.svg)](https://github.com/KindOfNerdy/ha-waipu/actions/workflows/validate.yml)

Unofficial Home Assistant integration for [waipu.tv](https://www.waipu.tv/),
a German IPTV streaming service. Surfaces EPG data and cloud-DVR control
in HA, and optionally couples with an existing Apple TV or Android TV
integration to launch the waipu app on the TV at the press of a button.

📖 **[Wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** — full entity/service
reference, Android TV channel-switching explained in depth, and worked
automation/script examples (this README stays a quick start).

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
| Launch the waipu app on Android TV | ✅ (app launch only — waipu has no channel deep links) |
| Switch channel on Android TV (service) | ⚠️ experimental — see [Android TV channel switching](#android-tv-channel-switching-experimental) |
| Record/stop recording a whole series (service) | ✅ both confirmed working live |
| Play the stream directly in HA | ❌ — blocked by Widevine DRM |

> The integration's entity *labels* are currently in German (`jetzt`, `danach`, `aufnahmen`, `wiedergabe`, …). The codebase otherwise speaks English; localisation can be reworked later if there's demand.

## Installation

### Option 1: HACS Custom Repository (recommended)

One-click add via the badge at the top of this README — it opens HACS on
your Home Assistant instance and registers this repository directly.

Or manually:

1. HACS → three-dot menu → *Custom repositories*
2. URL: `https://github.com/KindOfNerdy/ha-waipu`, category *Integration*
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
   - **Visible channels** — limits which stations get HA entities (a
     full waipu package can mean 300+ channels — pick the ones you care about)
   - **waipu app bundle id** — defaults to `de.exaring.waipu.tvos`. If
     wrong, read the actual bundle id from your Apple TV with pyatv on
     the HA host:
     ```bash
     atvremote --id <AppleTV-MAC> apps
     ```
   - **waipu app link** — defaults to `waipu://tv` (opens the app's live-TV
     view). Launching by bare package id (e.g. `de.exaring.waipu`) is
     unreliable on Android TV since a Google Play Store change — see the
     [androidtv_remote docs](https://www.home-assistant.io/integrations/androidtv_remote/)
     — so a deep link is used by default instead. Override this if you'd
     rather land on a different section (e.g. `waipu://epg`,
     `waipu://recordings`) or your device needs a different value (e.g. for
     `o2 TV powered by waipu.tv`).
   - **Channel number basis** — `Favorites only` (default) or `All
     channels`. Only relevant for the experimental
     [channel switching](#android-tv-channel-switching-experimental)
     service. When set to `Favorites only`, this also switches every HA
     entity this integration creates (sensors, recording buttons, the
     shared media_player's source list) to follow your waipu favorites
     live — "Visible channels" is ignored in that mode.
   - **Wait before channel switch on Android TV** — defaults to 4 seconds.
     `remote.turn_on` only confirms the TV's power state, not that the
     waipu app has actually finished cold-starting and is ready to accept
     channel-number key presses — too short a wait and the digits get
     silently ignored. Raise this if switching right after a cold start
     (TV/app was fully off) still doesn't land on the right channel; a
     quick app-switch while the TV is already on doesn't need nearly as
     long, but the same delay applies to both cases today.

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

As with Apple TV, this is app launch only: waipu exposes no channel-level
deep link on Android TV either, so the channel still has to be picked
manually on the TV after launch.

## Android TV channel switching (experimental)

`waipu.switch_channel_on_android_tv` can actually change the channel —
by sending the on-screen channel number as number-key presses via
`remote.send_command` (`androidtv_remote` exposes real Android TV
remote keycodes `"0"`–`"9"`), exactly like using a physical remote's
number pad.

**How the channel number is derived:** waipu doesn't expose a channel
number via its API — the number shown in the app is simply the channel's
position in your account's own channel list (1st channel → `1`, 8th → `8`,
etc.), confirmed by cross-checking the API's station order against the
app's own on-screen numbering. This integration recomputes that position
live from the same list order the API already returns, based on the
**Channel number basis** option (`All channels` or `Favorites only`).

**This only works if that setting matches what the waipu app on your
Android TV is currently displaying.** Whether the app shows all channels
or only favorites is a client-side app setting — Home Assistant has no way
to read or change it. If the two are out of sync, the service will switch
to the *wrong* channel (whatever number N actually is in the app's active
view), silently — there's no feedback path to detect this from HA. Pick
whichever mode you actually use on that TV, and keep it consistent with
the "Channel number basis" option.

```yaml
service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # required — the waipu station id to switch to
```

Given the app-state dependency above, treat this as a best-effort,
experimental feature rather than a fully reliable channel changer.

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
  source follow the real TV live. On Android TV, the card's
  next-track/previous-track buttons step the channel (experimental — see
  [Android TV channel switching](#android-tv-channel-switching-experimental)).
- a plain channel `select` dropdown, independent of the media_player —
  handy if your dashboard already uses the TV's own native media_player
  for turn on/off, volume, and other apps like Netflix.
- Three Android-TV-only shortcut buttons to jump straight to the app's
  TV/EPG/recordings views.

**waipu Aufnahmen** (recording management, DVR subscriptions only):

- the recordings `calendar` — every scheduled/ongoing/finished recording,
  with watched status and full EPG text where available.
- two sensors — unwatched / total recording counts, each with a `recordings` list
  attribute.

## Services

Full reference with more examples:
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Services-Reference)**.

```yaml
service: waipu.create_recording
data:
  station_id: ard          # required (lower-case waipu station id)
  program_id: "67ad0d26-…" # optional UUID — defaults to the currently airing program

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
# uses the Android TV configured in the integration options

service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # experimental — see the section above
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

- **No per-channel deep linking.** Neither the waipu tvOS nor the waipu
  Android TV app expose a public *deep link* to switch channels. After app
  launch the channel must be picked manually on Apple TV. On Android TV,
  there's an experimental workaround via number-key presses — see
  [Android TV channel switching](#android-tv-channel-switching-experimental)
  — but it depends on an app-side display setting HA can't verify, so
  treat it as best-effort, not a guaranteed channel changer.
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

## License

GPL-3.0 (inherited from the Kodi plugin lineage). See [LICENSE](LICENSE).
