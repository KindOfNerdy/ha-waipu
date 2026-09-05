# waipu.tv – Home Assistant Custom Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=GB-1972&repository=ha-waipu&category=integration)

Unofficial Home Assistant integration for [waipu.tv](https://www.waipu.tv/),
a German IPTV streaming service. Surfaces EPG data and cloud-DVR control
in HA, and optionally couples with an existing Apple TV or Android TV
integration to launch the waipu app on the TV at the press of a button.

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
   - **Android TV remote entity** — your existing `remote.*` entity from
     the official [androidtv_remote](https://www.home-assistant.io/integrations/androidtv_remote/)
     integration, e.g. `remote.living_room_android_tv`
   - **waipu app link** — defaults to `waipu://tv` (opens the app's live-TV
     view). Launching by bare package id (e.g. `de.exaring.waipu`) is
     unreliable on Android TV since a Google Play Store change — see the
     [androidtv_remote docs](https://www.home-assistant.io/integrations/androidtv_remote/)
     — so a deep link is used by default instead. Override this if you'd
     rather land on a different section (e.g. `waipu://epg`,
     `waipu://recordings`) or your device needs a different value (e.g. for
     `o2 TV powered by waipu.tv`).
   - **Channel number basis** — `All channels` (default) or `Favorites
     only`. Only relevant for the experimental
     [channel switching](#android-tv-channel-switching-experimental)
     service. When set to `Favorites only`, this also switches every HA
     entity this integration creates (sensors, recording buttons, the
     shared media_player's source list) to follow your waipu favorites
     live — "Visible channels" is ignored in that mode.

   Apple TV and Android TV are both entirely optional and independent of
   each other — set up one, both, or neither.

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
  selecting a source launches the waipu app on the configured TV. If both
  Apple TV and Android TV are configured, Apple TV takes precedence for
  this shared entity — use the dedicated services below to target either
  device explicitly. On Apple TV this is app launch only (channel picked
  manually afterward); on Android TV it also follows up with the
  experimental [channel switching](#android-tv-channel-switching-experimental)
  for the selected channel.
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

service: waipu.launch_on_android_tv
# uses the Android TV configured in the integration options

service: waipu.switch_channel_on_android_tv
data:
  station_id: swr_bw   # experimental — see the section above
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

## License

GPL-3.0 (inherited from the Kodi plugin lineage). See [LICENSE](LICENSE).
