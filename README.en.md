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
  the waipu card's channel picker, next/previous, or an automation, even
  while the app is running
- 🎬 **Play recordings on the TV** — tap one in the media browser and pick
  up where you left off
- 🗓️ **EPG as sensors** — what's on now and next, per channel, with images
- ⏺️ **Cloud recordings** — schedule, stop, delete, record whole series —
  plus a recordings calendar
- 🎛️ **Everything from the remote card** — the Live TV, Recordings, EPG and
  Media library sources jump straight to that section of the waipu app
- 👀 **Knows what's on the TV** — even when you switch channels on the TV
  itself, or watch a recording or a waiputhek movie (via Google Cast)
- ⏯️ **Pause, seek, restart** — right from the card; "restart program"
  starts the running live program over
- 🖼️ **Dashboard cards included** — player, "now on TV", recordings and a
  TV guide timeline, nothing extra to install

The 📖 **[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki)** has the full
entity/service reference, automation examples and ready-made dashboard
cards — this README is the quick start.

## What works — and what doesn't

| Feature | Status |
|---|---|
| Login (username/password, no 2FA) | ✅ |
| Channel list + station logos | ✅ |
| EPG: now-playing & next program per channel as a sensor | ✅ |
| Schedule a cloud recording (media browser, service, optional button per channel) | ✅ Perfect / Perfect Plus / O2 TV L/XL only |
| Stop an active recording early, delete recordings (service) | ✅ |
| Record/stop recording a whole series (service) | ✅ |
| List recordings (HA calendar, sensors) | ✅ |
| Switch channel on Android TV | ✅ directly via waipu link — see [Android TV channel switching](#android-tv-channel-switching) |
| Play a recording on Android TV | ✅ resume, from the start, or detail page — see [Recordings on Android TV](#recordings-on-android-tv) |
| See what's playing on the TV (channel, recording, waiputhek) | ✅ with the Google Cast entity — see [What's on the TV](#whats-on-the-tv-google-cast) |
| Pause/play, seek, restart program | ✅ Android TV; seeking in the waiputhek only with the Google Cast entity |
| Launch the waipu app on Apple TV | ✅ app launch only — no known channel links for tvOS |
| Play the stream directly in HA | ❌ blocked by Widevine DRM |

> Entity and device names follow your Home Assistant language: in English
> e.g. `ARD – now`, in German `ARD – jetzt`. The entity IDs in the examples
> assume a German-language Home Assistant.

## Installation

Requires Home Assistant **2025.8.0** or newer.

### Via the Marketplace / HACS (recommended)

1. Add the repository (*Add from link*, URL `https://github.com/KindOfNerdy/ha-waipu`, category *Integration*):

   [![Open your custom repositories in the Marketplace](https://my.home-assistant.io/badges/marketplace_repositories.svg)](https://my.home-assistant.io/redirect/marketplace_repositories/)

2. Open the repository in your Home Assistant:

   [![Open the repository in the Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   On older versions with HACS:

   [![Open the repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KindOfNerdy&repository=ha-waipu&category=integration)

   <details>
   <summary>Without the button</summary>

   On Home Assistant 2026.11 or newer: *Settings* → *Marketplace* → *Add
   from link*, URL `https://github.com/KindOfNerdy/ha-waipu`, category
   *Integration*. On older versions with HACS: HACS → three-dot menu →
   *Custom repositories*, same URL and category.
   </details>

3. Install **waipu.tv**.
4. Restart Home Assistant.

### Manually

Copy the `custom_components/waipu/` folder to
`<HA-config>/custom_components/waipu/` and restart Home Assistant.

## Setup

1. Add the integration:

   [![Set up the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=waipu)

   or *Settings* → *Devices & services* → *Add integration* → **waipu.tv**.
2. Enter your waipu email and password. They're only used to log in; the
   entry is named after your plan (e.g. "Perfect Plus"), not your email.
   In your waipu account the sign-in shows up under *Devices* as
   "Home Assistant (ha-waipu …)". waipu keeps at most five sign-ins; a new
   one pushes out the oldest. If that hits Home Assistant, the integration
   signs in again with the stored password by itself — pushing out the
   then-oldest device in turn. So remove entries you no longer use there.
3. **Choose your TV** — Android TV, Apple TV (app launch only) or none — and
   pick its entity on the next page:
   - **Android TV:** the `remote.*` entity from the official
     [Android TV Remote integration](https://www.home-assistant.io/integrations/androidtv_remote/)
     (see [Android TV](#android-tv))
   - **Apple TV:** the `media_player` from the Apple TV integration

Everything can be changed later under *Configure*.

### Options

*Configure* opens up to three pages: first TV and channel selection, then
the chosen TV's fields, and with "All channels" finally the channel list.

| Option | Meaning |
|---|---|
| **TV** | Android TV, Apple TV or none. There's always exactly one; switching removes the previous one's settings. |
| **Channel selection** | Which channels get HA entities. `Favorites` (default) follows your waipu favorites live. With `All channels` you pick them on a separate page under **Visible channels**; the selection is kept even if you switch to `Favorites` in between. |
| **Google Cast entity** (Android TV, optional) | The TV's `media_player` from the [Google Cast integration](https://www.home-assistant.io/integrations/cast/). Lets the integration see what's playing on the TV and seek in the waiputhek — see [What's on the TV](#whats-on-the-tv-google-cast). |
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
- **next/previous** on the media_player card — next/previous channel in
  your channel list, wrapping around at the end
- in automations and scripts, `media_player.play_media` with the waipu
  station id:

```yaml
action: media_player.play_media
target:
  entity_id: media_player.waipu_wiedergabe
data:
  media_content_type: channel
  media_content_id: swr_bw   # the waipu station id, e.g. from the media_player's station_id attribute
```

Switching takes a brief moment while the app loads the channel. The channel
order or view in the waipu app doesn't matter.

## Recordings on Android TV

Easiest via the **media browser**: tap "Browse media" on the media_player
card (or open *Media* in the sidebar).

- **Recordings** — every finished or ongoing recording, watched or not,
  newest first, with preview image. Several episodes of the same series
  are grouped in their own folder; series folders come first, sorted by
  title. Tapping a recording plays it on the TV,
  resuming where you left off — fully watched ones start from the
  beginning.
- **Channels** — your channel list; tapping one switches to it.
- **TV guide** — per channel the running and upcoming programs of the next
  few hours. Tapping the running program plays it live. An upcoming one
  opens the choice **Details on the TV**, **Record episode** and **Record
  series** — recording goes straight through waipu, the TV doesn't need to
  be on. Already scheduled programs are marked "⏺ scheduled" and offer
  **Cancel recording**; if a series recording already runs for the series,
  **Stop series recording** replaces "Record series" (what's recorded stays). Where recording isn't allowed (plan, channel or
  program), an upcoming program opens its detail page directly. To start the
  running program over, use `waipu.restart_program` (see
  [What's on the TV](#whats-on-the-tv-google-cast)).

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

## What's on the TV (Google Cast)

The Android TV Remote integration only tells *which app* is in front, not
the channel. The [Google Cast integration](https://www.home-assistant.io/integrations/cast/)
however sets up a `media_player` for many Android TVs on its own, and it
reports what the waipu app is playing. It's usually named after your TV;
the right one shows `waipu.tv` as its app while waipu is playing. Select it
under *Configure → Android TV* as the **Google Cast entity**, and the waipu
card always shows what's really on:

| On the TV | Source on the card | Shown |
|---|---|---|
| live TV | Live TV | channel and current program — also after switching on the TV itself |
| live, paused or restarted | Live TV | the program you're actually watching, and how many minutes you're behind live (`timeshift_minutes`) |
| a recording | Recordings | title, the channel it was recorded from, progress bar |
| a waiputhek movie | Media library | title, image, progress bar |

It also adds controls:

- **Pause/play** on the card (without a Cast entity via the remote's
  play/pause key). Missing for programs waipu doesn't let you pause.
- **Seek** with the progress bar in recordings and the waiputhek. Seeking
  past an ad break, waipu shows the ads first and then jumps to the chosen
  spot by itself. Recordings also work without a Cast entity — waipu then
  briefly reloads. Live, you can jump within the running program too
  (`media_player.media_seek` with a Unix time, e.g. the waipu card's ±30 s
  buttons) — no Cast entity needed.
- **Restart program** with `waipu.restart_program` — this works without a
  Cast entity too. The `restart_available` attribute tells whether the
  running program allows it — some channels (e.g. ProSieben, SAT.1) don't
  allow seeking live.

Next/previous on the card still switches the channel.

## Generated entities

Entities land on three devices. Exact entity IDs depend on your setup —
check *Developer Tools → States* for yours. Full reference:
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Entities-Reference)**.

**waipu Wiedergabe** — TV control

- **`media_player`** — the remote card for waipu: on/off and volume go to
  the TV, its state follows the TV live.
  - **media browser** with *Recordings*, *Channels* and *TV guide*
  - **sources** Live TV, Recordings, EPG and Media library jump straight to
    that section of the waipu app; EPG opens on the tuned channel (Android TV)
  - **next/previous** switches the channel (Android TV)
  - title and image of what's playing — with the Google Cast entity also
    recordings and the waiputhek, with pause, progress bar and seeking
  - attribute `channels` — your channel list, e.g. for a channel picker in
    your own dashboard cards
- four **shortcut buttons** for Live TV, EPG, Recordings and Media library —
  same as the sources (Android TV)

**waipu Senderübersicht** — one set per channel in the channel selection

- `sensor.<station>_jetzt` / `_danach` — current/next program with EPG
  details (description, age rating, episode, genre). `_danach` lists
  further `upcoming` programs with `program_id` and `series_id` for
  recording.
- a button per channel that records what's on right now (DVR plan)

The record button starts disabled — recording also works from the media
browser or with `waipu.create_recording`. Turn it on under *Settings →
Devices & services → waipu.tv → Entities* if you want it.

**waipu Aufnahmen** — DVR plans only

- **calendar** with every scheduled, ongoing and finished recording
- two **sensors** — count of new and of all recordings, each with a
  `recordings` list (including `recording_id`, channel, `position_percentage` and image)
- **Free recording space** — how many hours can still be recorded, as the
  app shows it; plus used hours and the number of recordings

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
| `waipu.play_recording_on_android_tv` | play a recording on the Android TV |
| `waipu.restart_program` | start the running live program on the Android TV over |
| `waipu.open_program_on_android_tv` | open a program's detail page on the Android TV (or play it with `autoplay`) — without arguments the running program of the tuned channel |

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

## Dashboard cards

The integration comes with four cards. They're in the card picker right after
installing, no resource to add; colors and fonts come from your theme. They
all find the waipu player themselves — you only need `entity` if you have
more than one.

### waipu.tv Player

- picture, title, channel and episode of what's on — with *Live*,
  *Recording* or *Media library*, how far behind live you are and whether it's
  being recorded
- progress: the air time when live, the position for recordings and
  the media library
- buttons for previous/next channel, pause/play, 30 seconds back/forward
  (live too), "From the start" and record/stop recording — only the ones that work
  right now
- channel picker with the channel's logo, and power

```yaml
type: custom:waipu-card
```

Under a remote or in a pop-up, `mode: compact` fits better — a small picture,
what's on and the channel picker. `mode: row` is a single line like a tile,
e.g. for a "now playing" list: picture, what's on, how long it has left and
one button (pause/play, otherwise power); tapping opens the details.

```yaml
type: custom:waipu-card
mode: compact
hide: [off_hint]   # without "TV is off": just the channel picker while the TV is off
```

| Option | Meaning |
|---|---|
| `mode` | `full` (default), `compact` or `row` |
| `hide` | parts to leave out: `picture`, `progress`, `controls`, `record`, `channels`, `off_hint`. Compact hides `controls` unless you set `hide` yourself. |
| `tap_action` | with `row`: what a tap does (default: open the details) |

### waipu.tv Now on TV

Every channel with what's on now, its progress and what's next. Tap to
switch; next to it record or stop. Expanded: the description, "Record next",
"Record series" and "Details on TV".

```yaml
type: custom:waipu-channels-card
channels: [ard, zdf]   # optional: only these channels
```

### waipu.tv Recordings

Your cloud recordings with picture and progress, in the tabs *New*,
*Available* and *Planned*. Tap to play on the TV; deleting or cancelling asks
once, running recordings can be stopped.

```yaml
type: custom:waipu-recordings-card
tab: available   # optional: new, available or planned
max: 20          # optional: at most this many entries
```

### waipu.tv TV guide

The next six hours as a timeline with a "now" line. Tap a program: watch it
(if it's on now), details on the TV, record, record the series or cancel a
planned recording.

```yaml
type: custom:waipu-guide-card
channels: [ard, zdf]   # optional
```

"Details on TV" and "From the start" need a connected Android TV.

Just the channel picker, as a row in an entities card:
`- type: custom:waipu-channel-row`. Pause, seeking and showing recordings
and the media library need the Google Cast entity. Cards made of
built-in parts only are in the
**[wiki](https://github.com/KindOfNerdy/ha-waipu/wiki/Dashboard-Cards)**.

## Known limitations

- **Apple TV: app launch only.** No links are known for the waipu tvOS app
  that would open a channel or recording directly. On Android TV both work.
- **Ads can't be detected.** During ads Google Cast reports the same
  program; the progress bar simply keeps running.
- **Single waiputhek movies can't be started from HA.** The media library
  itself opens, but a specific movie needs ids the integration doesn't know.
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
identification only. The media browser icons are from
[Material Design Icons](https://pictogrammers.com/library/mdi/) (Apache-2.0).
