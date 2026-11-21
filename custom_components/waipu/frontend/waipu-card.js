/*
 * waipu.tv cards for Home Assistant
 * Dashboard cards for the waipu.tv integration (KindOfNerdy/ha-waipu):
 *   waipu-card            the player (mode full, compact or row)
 *   waipu-channels-card   what's on now and next, per channel
 *   waipu-recordings-card the cloud recordings
 *   waipu-guide-card      the TV guide as a timeline
 *   waipu-reminders-card  reminders that switch the TV at the start
 *   waipu-channel-row     a channel picker row for entities cards
 * Colors and fonts come only from the Home Assistant theme.
 */

// The integration serves this file as …/waipu-card.js?v=<its version>.
const CARD_VERSION = new URL(import.meta.url).searchParams.get("v") || "dev";
const DOMAIN = "waipu";

const TEXT = {
  en: {
    no_player: "No waipu.tv player found. Set up the waipu.tv integration first.",
    off: "TV is off",
    idle: "Nothing playing",
    unknown_channel: "waipu is open",
    live: "Live",
    recording: "Recording",
    mediathek: "Media library",
    behind: "{min} min behind live",
    channel: "Channel",
    pick_channel: "Pick a channel",
    power_on: "Switch on",
    power_off: "Switch off",
    previous: "Previous channel",
    next: "Next channel",
    play: "Play",
    pause: "Pause",
    back: "Back 30 seconds",
    forward: "Forward 30 seconds",
    restart: "From the start",
    record: "Record",
    stop_record: "Stop recording",
    recording_now: "Recording",
    left: "{min} min left",
    until: "until {time}",
    failed: "That didn't work: {error}",
    // channels card
    channels_title: "Now on TV",
    no_channels: "No channels yet — the integration hasn't loaded the program guide.",
    then: "Then",
    record_next: "Record next",
    record_now: "Record",
    switch_here: "Switch to it",
    record_series: "Record series",
    details_tv: "Details on TV",
    watch: "Watch",
    tuned: "On the TV",
    more: "More",
    // recordings card
    recordings_title: "Recordings",
    no_dvr: "Your waipu plan has no cloud recordings.",
    tab_new: "New",
    tab_available: "Available",
    tab_planned: "Planned",
    empty_new: "No new recordings.",
    empty_available: "No recordings yet. Record something from the guide or the channel list.",
    empty_planned: "Nothing planned.",
    new_badge: "New",
    running: "Recording now",
    delete: "Delete",
    cancel_rec: "Cancel",
    confirm_delete: "Really delete?",
    confirm_cancel: "Really cancel?",
    play_tv: "Play on TV",
    watched: "Watched",
    // guide card
    guide_title: "TV guide",
    loading: "Loading the guide …",
    planned: "Planned",
    now_line: "Now",
    close: "Close",
    // editors
    ed_entity: "waipu player (only needed with more than one)",
    ed_mode: "Mode",
    ed_mode_full: "Full: big picture and controls",
    ed_mode_compact: "Compact: small picture and channel picker, e.g. under a remote",
    ed_mode_row: "Row: one line like a tile, e.g. in a \"now playing\" list",
    ed_hide: "Hide",
    ed_hide_picture: "Picture",
    ed_hide_progress: "Progress bar",
    ed_hide_controls: "Controls",
    ed_hide_record: "Record button",
    ed_hide_channels: "Channel picker",
    ed_hide_off_hint: "\"TV is off\" line with its power button",
    ed_name: "Title",
    ed_channels: "Only these channels (ids, empty = all)",
    ed_tab: "Tab to start with",
    ed_max: "At most this many entries",
    ed_tap_action: "Tap action",
    // reminders
    remind: "Remind me",
    remind_series: "Remind of series",
    remind_next: "Remind of next",
    remind_remove: "Remove reminder",
    reminders_title: "Reminders",
    no_reminders: "No reminders yet. Tap a program in the TV guide and choose \"Remind me\" — or add a schedule.",
    switches_to: "Switches to {station}",
    reminds_of: "Reminds of {station}",
    today: "today",
    tomorrow: "tomorrow",
    off_short: "Off",
    kind_program: "Program",
    kind_series: "Series",
    daily: "Daily",
    weekdays: "Mon–Fri",
    weekend: "Weekend",
    once: "once",
    only_once: "Only once",
    switch_at_start: "Switch at start",
    skip_next: "Skip next time",
    unskip: "Don't skip",
    skipped: "Skipped next time",
    add_schedule: "Add schedule",
    time: "Time",
    save: "Save",
    cancel: "Cancel",
    reminder_on: "Reminder on",
    card_player: "waipu.tv Player",
    card_player_text: "What's on the TV with picture and progress, controls, record button and a channel picker — full, compact or as a row.",
    card_channels: "waipu.tv Now on TV",
    card_channels_text: "Every channel with what's on now and next; tap to switch, record now, next or the series.",
    card_recordings: "waipu.tv Recordings",
    card_recordings_text: "Your cloud recordings with pictures — new, available and planned; play on the TV, stop or delete.",
    card_guide: "waipu.tv TV guide",
    card_guide_text: "The next hours as a timeline; watch, record or open details on the TV.",
    card_reminders: "waipu.tv Reminders",
    card_reminders_text: "Push before a program, series or time slot and switch the TV at its start.",
  },
  de: {
    no_player: "Kein waipu.tv-Player gefunden. Richte zuerst die Integration waipu.tv ein.",
    off: "Fernseher ist aus",
    idle: "Gerade läuft nichts",
    unknown_channel: "waipu ist offen",
    live: "Live",
    recording: "Aufnahme",
    mediathek: "Mediathek",
    behind: "{min} min hinter live",
    channel: "Sender",
    pick_channel: "Sender wählen",
    power_on: "Einschalten",
    power_off: "Ausschalten",
    previous: "Vorheriger Sender",
    next: "Nächster Sender",
    play: "Abspielen",
    pause: "Pause",
    back: "30 Sekunden zurück",
    forward: "30 Sekunden vor",
    restart: "Von vorn",
    record: "Aufnehmen",
    stop_record: "Aufnahme stoppen",
    recording_now: "Wird aufgenommen",
    left: "noch {min} min",
    until: "bis {time}",
    failed: "Das hat nicht geklappt: {error}",
    channels_title: "Jetzt im TV",
    no_channels: "Noch keine Sender — die Integration hat das Programm noch nicht geladen.",
    then: "Danach",
    record_next: "Danach aufnehmen",
    record_now: "Aufnehmen",
    switch_here: "Umschalten",
    record_series: "Serie aufnehmen",
    details_tv: "Details am TV",
    watch: "Ansehen",
    tuned: "Läuft am TV",
    more: "Mehr",
    recordings_title: "Aufnahmen",
    no_dvr: "Dein waipu-Paket hat keine Cloud-Aufnahmen.",
    tab_new: "Neu",
    tab_available: "Verfügbar",
    tab_planned: "Geplant",
    empty_new: "Keine neuen Aufnahmen.",
    empty_available: "Noch keine Aufnahmen. Nimm etwas aus dem Programm oder der Senderliste auf.",
    empty_planned: "Nichts geplant.",
    new_badge: "Neu",
    running: "Läuft gerade",
    delete: "Löschen",
    cancel_rec: "Abbrechen",
    confirm_delete: "Wirklich löschen?",
    confirm_cancel: "Wirklich abbrechen?",
    play_tv: "Am TV abspielen",
    watched: "Gesehen",
    guide_title: "Programm",
    loading: "Programm wird geladen …",
    planned: "Geplant",
    now_line: "Jetzt",
    close: "Schließen",
    ed_entity: "waipu-Player (nur nötig, wenn es mehrere gibt)",
    ed_mode: "Darstellung",
    ed_mode_full: "Voll: großes Bild und Steuerung",
    ed_mode_compact: "Kompakt: kleines Bild und Senderauswahl, z. B. unter einer Fernbedienung",
    ed_mode_row: "Zeile: eine Zeile wie eine Kachel, z. B. in einer „Läuft gerade“-Liste",
    ed_hide: "Ausblenden",
    ed_hide_picture: "Bild",
    ed_hide_progress: "Fortschrittsbalken",
    ed_hide_controls: "Steuerung",
    ed_hide_record: "Aufnahme-Knopf",
    ed_hide_channels: "Senderauswahl",
    ed_hide_off_hint: "Zeile „Fernseher ist aus“ samt Ein-Knopf",
    ed_name: "Überschrift",
    ed_channels: "Nur diese Sender (IDs, leer = alle)",
    ed_tab: "Reiter beim Öffnen",
    ed_max: "Höchstens so viele Einträge",
    ed_tap_action: "Aktion beim Antippen",
    remind: "Erinnern",
    remind_series: "Serie erinnern",
    remind_next: "Danach erinnern",
    remind_remove: "Erinnerung entfernen",
    reminders_title: "Erinnerungen",
    no_reminders: "Noch keine Erinnerungen. Im Programm eine Sendung antippen und „Erinnern“ wählen – oder einen Zeitplan anlegen.",
    switches_to: "Schaltet auf {station}",
    reminds_of: "Erinnert an {station}",
    today: "heute",
    tomorrow: "morgen",
    off_short: "Aus",
    kind_program: "Sendung",
    kind_series: "Serie",
    daily: "Täglich",
    weekdays: "Mo–Fr",
    weekend: "Wochenende",
    once: "einmalig",
    only_once: "Nur einmal",
    switch_at_start: "Zu Beginn umschalten",
    skip_next: "Nächstes Mal auslassen",
    unskip: "Doch nicht auslassen",
    skipped: "Nächstes Mal ausgelassen",
    add_schedule: "Zeitplan anlegen",
    time: "Uhrzeit",
    save: "Speichern",
    cancel: "Abbrechen",
    reminder_on: "Erinnerung an",
    card_player: "waipu.tv Player",
    card_player_text: "Was am Fernseher läuft, mit Bild und Fortschritt, Steuerung, Aufnahme-Knopf und Senderauswahl — voll, kompakt oder als Zeile.",
    card_channels: "waipu.tv Jetzt im TV",
    card_channels_text: "Jeder Sender mit der laufenden und der nächsten Sendung; antippen schaltet um, aufnehmen jetzt, danach oder die Serie.",
    card_recordings: "waipu.tv Aufnahmen",
    card_recordings_text: "Deine Cloud-Aufnahmen mit Bild — neu, verfügbar und geplant; am TV abspielen, stoppen oder löschen.",
    card_guide: "waipu.tv Programm",
    card_guide_text: "Die nächsten Stunden als Zeitleiste; ansehen, aufnehmen oder Details am TV öffnen.",
    card_reminders: "waipu.tv Erinnerungen",
    card_reminders_text: "Push vor einer Sendung, Serie oder Uhrzeit und zu Beginn auf den Sender umschalten.",
  },
};

// Media player feature bits (homeassistant.components.media_player)
const F = { PAUSE: 1, SEEK: 2, PREVIOUS: 16, NEXT: 32, TURN_ON: 128, TURN_OFF: 256, PLAY: 16384 };
const HIDE_KEYS = ["picture", "progress", "controls", "record", "channels", "off_hint"];
const MODES = ["full", "compact", "row"];
const SEEK_STEP = 30;
const CONFIRM_MS = 4000;

// --- helpers ------------------------------------------------------------------
function lang(hass) {
  const l = hass?.locale?.language || hass?.language || navigator.language || "en";
  return l.toLowerCase().startsWith("de") ? "de" : "en";
}

function uiText(key, hass) {
  const l = hass ? lang(hass) : (navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en";
  return TEXT[l][key] ?? TEXT.en[key] ?? key;
}

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// Playback position as 1:05:09 or 5:09.
function clock(seconds) {
  const t = Math.max(0, Math.floor(seconds));
  const h = Math.floor(t / 3600);
  const m = Math.floor((t % 3600) / 60);
  const sec = String(t % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

function timeOf(hass, iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString(lang(hass), { hour: "2-digit", minute: "2-digit" });
}

function dayTimeOf(hass, iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const opts = { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" };
  return d.toLocaleString(lang(hass), opts);
}

// Progress of a program's air time: percent done and minutes left.
function airProgress(startIso, stopIso, lagSeconds = 0) {
  const start = new Date(startIso).getTime();
  const stop = new Date(stopIso).getTime();
  if (!(stop > start)) return null;
  const now = Date.now() - lagSeconds * 1000;
  const pct = Math.min(Math.max(((now - start) / (stop - start)) * 100, 0), 100);
  return { pct, left: Math.max(Math.round((stop - now) / 60000), 0) };
}

function has(stateObj, bit) {
  return ((stateObj?.attributes?.supported_features || 0) & bit) === bit;
}

// The integration's entities, found by platform and translation key — no
// entity ids to configure.
function findEntities(hass, config) {
  const entries = Object.values(hass?.entities || {}).filter((e) => e.platform === DOMAIN);
  const players = entries.filter((e) => e.entity_id.startsWith("media_player."));
  const player = config?.entity || players[0]?.entity_id || null;
  const recordings = entries.find((e) => e.translation_key === "all_recordings")?.entity_id || null;
  const reminders = entries.find((e) => e.translation_key === "reminders")?.entity_id || null;
  // Now/next sensors per channel, keyed by the station id they report.
  const programs = {};
  for (const e of entries) {
    if (e.translation_key !== "now" && e.translation_key !== "next") continue;
    const s = hass.states[e.entity_id];
    const sid = s?.attributes?.station_id;
    if (!sid) continue;
    programs[sid] = programs[sid] || {};
    programs[sid][e.translation_key] = s;
  }
  return { player, recordings, reminders, programs };
}

function channelsOf(stateObj) {
  const list = stateObj?.attributes?.channels;
  return Array.isArray(list) ? list : [];
}

function recordingsOf(hass, recordingsEntity) {
  const list = recordingsEntity ? hass.states[recordingsEntity]?.attributes?.recordings : null;
  return Array.isArray(list) ? list : [];
}

// The reminders sensor: the reminders and their coming starts.
function remindersOf(hass, entity) {
  const a = entity ? hass.states[entity]?.attributes : null;
  return { list: Array.isArray(a?.reminders) ? a.reminders : [], upcoming: Array.isArray(a?.upcoming) ? a.upcoming : [] };
}

// The reminder covering a program, if any (the program itself or its series).
function reminderFor(rem, stationId, program) {
  return (
    rem.list.find((r) => r.kind === "program" && r.program_id === program.id) ||
    rem.list.find((r) => r.kind === "series" && r.enabled && r.station_id === stationId && program.series_id && r.series_id === program.series_id) ||
    null
  );
}

function channelSelect(hass, player, stateObj) {
  const channels = channelsOf(stateObj);
  if (!channels.length) return "";
  const current = stateObj.attributes.station_id;
  const active = channels.find((c) => c.id === current);
  // Only a real channel logo goes in front; without one the text starts left.
  const logo = active?.logo ? `<img class="logo" src="${esc(active.logo)}" alt="">` : "";
  return `
    <label class="pick ${logo ? "" : "nologo"}">
      ${logo}
      <select data-act="channel" data-entity="${esc(player)}" aria-label="${esc(uiText("channel", hass))}">
        ${active ? "" : `<option value="" selected disabled>${esc(uiText("pick_channel", hass))}</option>`}
        ${channels
          .map((c) => `<option value="${esc(c.id)}" ${c.id === current ? "selected" : ""}>${esc(c.name)}</option>`)
          .join("")}
      </select>
      <ha-icon class="chev" icon="mdi:unfold-more-horizontal"></ha-icon>
    </label>`;
}

// What a tap does — the subset of HA's card actions these cards offer.
function runAction(el, hass, action, defaultEntity) {
  const a = action || { action: "more-info" };
  const fire = (type, detail) =>
    el.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
  switch (a.action) {
    case "none":
      return;
    case "navigate":
      if (!a.navigation_path) return;
      history.pushState(null, "", a.navigation_path);
      fire("location-changed", { replace: false });
      return;
    case "url":
      if (a.url_path) window.open(a.url_path, "_blank");
      return;
    case "perform-action":
    case "call-service": {
      const [domain, service] = (a.perform_action || a.service || "").split(".");
      if (domain && service) hass.callService(domain, service, a.data || a.service_data || {}, a.target);
      return;
    }
    default:
      fire("hass-more-info", { entityId: a.entity || defaultEntity });
  }
}

// --- shared styles ------------------------------------------------------------
const BASE_CSS = `
  :host { display: block; container-type: inline-size; }
  ha-card { overflow: hidden; }
  button { all: unset; box-sizing: border-box; cursor: pointer; display: inline-flex; align-items: center;
    justify-content: center; position: relative; -webkit-tap-highlight-color: transparent; }
  button:focus-visible, [role="button"]:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  button[disabled] { cursor: default; }
  .empty { padding: 16px; color: var(--secondary-text-color); }
  .msg { font-size: 13px; color: var(--error-color); padding: 0 16px 12px; }
  .chip { gap: 6px; height: 36px; padding: 0 14px 0 10px; border-radius: 18px; font-size: 14px; font-weight: 500;
    color: var(--primary-color); border: 1px solid color-mix(in srgb, var(--primary-color) 55%, transparent);
    --mdc-icon-size: 18px; white-space: nowrap; }
  .chip:hover { background: color-mix(in srgb, var(--primary-color) 12%, transparent); }
  .chip.rec { color: var(--error-color); border-color: color-mix(in srgb, var(--error-color) 55%, transparent); }
  .chip.rec:hover { background: color-mix(in srgb, var(--error-color) 12%, transparent); }
  .chip.confirm { background: var(--error-color); color: var(--text-primary-color); border-color: var(--error-color); }
  .bar { height: 4px; border-radius: 2px; background: var(--divider-color); overflow: hidden; }
  .bar div { height: 100%; background: var(--accent-color); transition: width 1s linear; }
  .live { display: inline-flex; align-items: center; gap: 6px; color: var(--error-color); font-weight: 600; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--error-color); animation: onair 2s ease-in-out infinite; }
  @keyframes onair { 50% { opacity: .35; } }
  .rec-mark { display: inline-flex; align-items: center; gap: 4px; color: var(--error-color); }
  .rec-mark ha-icon { --mdc-icon-size: 16px; }
  /* Waiting for the TV or waipu: the pressed button spins until it's done. */
  .busy > ha-icon, .busy > span { visibility: hidden; }
  .busy::after { content: ""; position: absolute; width: 18px; height: 18px; border-radius: 50%;
    border: 2px solid currentColor; border-right-color: transparent; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) { .dot { animation: none; } .busy::after { animation-duration: 2s; } }
`;

// The picker: a field with the channel's logo in front and a chevron behind,
// so it reads as something to open.
const PICK_CSS = `
  .pick { position: relative; display: flex; align-items: center; min-width: 0; height: 44px;
    border: 1px solid var(--divider-color); border-radius: 22px; background: var(--secondary-background-color);
    transition: border-color .15s; }
  .pick:hover { border-color: var(--primary-color); }
  .pick:focus-within { border-color: var(--primary-color); box-shadow: 0 0 0 1px var(--primary-color); }
  .pick .logo { position: absolute; left: 6px; width: 48px; height: 32px; object-fit: contain; pointer-events: none; }
  .pick select { all: unset; box-sizing: border-box; width: 100%; height: 100%; padding: 0 40px 0 62px; cursor: pointer;
    line-height: 42px; color: var(--primary-text-color); font-size: 15px; font-weight: 500;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pick select option { background: var(--card-background-color); color: var(--primary-text-color); }
  .pick.nologo select { padding-left: 16px; }
  .pick .chev { position: absolute; right: 12px; pointer-events: none; color: var(--primary-color); --mdc-icon-size: 20px; }
`;

// --- base ---------------------------------------------------------------------
// Shared behaviour of every card and the row: redraw only when something shown
// changed (never while a drop-down is open), a channel drop-down that switches,
// service calls with a waiting state per button, and a short error line.
class WaipuBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._message = "";
    this._sig = null;
    this._busy = new Set();
    this._confirm = null;
    this.shadowRoot.addEventListener("change", (e) => {
      const sel = e.target.closest("select[data-act='channel']");
      if (!sel || !sel.value) return;
      this._call("channel", "media_player", "play_media", {
        entity_id: sel.dataset.entity,
        media_content_type: "channel",
        media_content_id: sel.value,
      });
      sel.blur();
    });
    this.shadowRoot.addEventListener("focusout", () => {
      if (!this._held) return;
      this._held = false;
      setTimeout(() => this._render(), 0);
    });
    this.shadowRoot.addEventListener("click", (e) => {
      const el = e.target.closest("[data-act]");
      if (!el || el.disabled || el.tagName === "SELECT") return;
      e.stopPropagation();
      this._act(el.dataset.act, el.dataset);
    });
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _t(key) {
    return uiText(key, this._hass);
  }

  _act() {}

  _render(force = false) {
    if (!this._hass || !this._config) return;
    const sig = JSON.stringify([this._signature(), this._message, [...this._busy], this._confirm, lang(this._hass)]);
    if (!force && sig === this._sig) return;
    // Never redraw under an open drop-down or a field being typed in.
    if (!force && ["SELECT", "INPUT"].includes(this.shadowRoot.activeElement?.tagName)) {
      this._held = true;
      return;
    }
    this._sig = sig;
    this._draw();
  }

  // Run a service call; the button with data-key = `key` spins meanwhile.
  async _call(key, domain, service, data) {
    this._busy.add(key);
    this._render(true);
    try {
      await this._hass.callService(domain, service, data);
    } catch (err) {
      this._message = this._t("failed").replace("{error}", err?.message || err);
      clearTimeout(this._messageTimer);
      this._messageTimer = setTimeout(() => {
        this._message = "";
        this._render(true);
      }, 6000);
    } finally {
      this._busy.delete(key);
      this._render(true);
    }
  }

  // First tap arms, second tap (within a few seconds) confirms.
  _armed(key) {
    if (this._confirm === key) {
      this._confirm = null;
      return true;
    }
    this._confirm = key;
    clearTimeout(this._confirmTimer);
    this._confirmTimer = setTimeout(() => {
      this._confirm = null;
      this._render(true);
    }, CONFIRM_MS);
    this._render(true);
    return false;
  }

  _bz(key) {
    return this._busy.has(key) ? "busy" : "";
  }

  _iconButton(act, icon, label, cls = "", data = "") {
    const key = act + data;
    return `<button class="ctl ${cls} ${this._bz(key)}" data-act="${act}" ${data ? `data-id="${esc(data)}"` : ""}
      title="${esc(label)}" aria-label="${esc(label)}" ${this._busy.has(key) ? "disabled" : ""}><ha-icon icon="${icon}"></ha-icon></button>`;
  }

  _chip(act, icon, label, cls = "", data = "") {
    const key = act + data;
    return `<button class="chip ${cls} ${this._bz(key)}" data-act="${act}" ${data ? `data-id="${esc(data)}"` : ""}
      ${this._busy.has(key) ? "disabled" : ""}><ha-icon icon="${icon}"></ha-icon><span>${esc(label)}</span></button>`;
  }

  _messageHtml() {
    return this._message ? `<div class="msg" role="alert">${esc(this._message)}</div>` : "";
  }
}

// --- player -------------------------------------------------------------------
class WaipuCard extends WaipuBase {
  constructor() {
    super();
    // In row mode the whole line is a tap target (its own action).
    this.shadowRoot.addEventListener("click", (e) => {
      if (this._config?.mode !== "row" || e.target.closest("[data-act]")) return;
      if (!e.target.closest(".row")) return;
      runAction(this, this._hass, this._config.tap_action, this._ids().player);
    });
    this.shadowRoot.addEventListener("keydown", (e) => {
      if (this._config?.mode === "row" && (e.key === "Enter" || e.key === " ") && e.target.classList?.contains("row")) {
        e.preventDefault();
        runAction(this, this._hass, this._config.tap_action, this._ids().player);
      }
    });
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
        {
          name: "mode",
          default: "full",
          selector: { select: { mode: "list", options: MODES.map((k) => ({ value: k, label: uiText(`ed_mode_${k}`) })) } },
        },
        {
          name: "hide",
          selector: {
            select: {
              multiple: true,
              mode: "list",
              options: HIDE_KEYS.map((k) => ({ value: k, label: uiText(`ed_hide_${k}`) })),
            },
          },
        },
        { name: "tap_action", selector: { ui_action: {} } },
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (config.hide && !Array.isArray(config.hide)) throw new Error("hide must be a list");
    // `layout` was the name in 2.2.0 betas; `mode` matches the other cards.
    const mode = config.mode || config.layout || "full";
    if (!MODES.includes(mode)) throw new Error("mode must be full, compact or row");
    // Compact sits under a remote: no transport controls unless asked for.
    const hide = config.hide || (mode === "compact" ? ["controls"] : []);
    const { layout, ...rest } = config;
    this._config = { ...rest, mode, hide };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return { full: 5, compact: 2, row: 1 }[this._config?.mode] || 5;
  }

  getGridOptions() {
    if (this._config?.mode === "row") return { rows: 1, columns: 12, min_columns: 6 };
    return { columns: 12, min_columns: 6 };
  }

  connectedCallback() {
    // Live progress moves with the clock, on-demand progress with the position.
    this._tick = setInterval(() => this._updateProgress(), 1000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  _hidden(key) {
    return this._config.hide.includes(key);
  }

  _ids() {
    return findEntities(this._hass, this._config);
  }

  _signature() {
    const { player, recordings } = this._ids();
    const s = this._hass.states[player];
    const r = recordings ? this._hass.states[recordings] : null;
    return [player, s?.state, s?.attributes, r?.last_updated, this._config];
  }

  // What plays right now, derived from the player's state and attributes.
  _playing(s) {
    const a = s.attributes;
    const off = s.state === "off" || s.state === "unavailable";
    const onDemand = a.source && a.media_duration != null;
    let kind = null;
    if (a.recording_id) kind = "recording";
    else if (a.station_id) kind = "live";
    else if (a.media_title && a.source) kind = "mediathek";
    return { off, onDemand: onDemand || kind === "recording" || kind === "mediathek", kind };
  }

  // A recording running on the tuned channel — the one waipu.stop_recording stops.
  _isRecording(s) {
    if (!s.attributes.station_id) return false;
    return recordingsOf(this._hass, this._ids().recordings).some(
      (r) => r.status === "RECORDING" && r.station_id === s.attributes.station_id
    );
  }

  _progress(s) {
    const a = s.attributes;
    if (a.media_duration) {
      let pos = Number(a.media_position || 0);
      if (s.state === "playing" && a.media_position_updated_at) {
        pos += (Date.now() - new Date(a.media_position_updated_at).getTime()) / 1000;
      }
      pos = Math.min(Math.max(pos, 0), a.media_duration);
      return { pct: (pos / a.media_duration) * 100, left: Math.round((a.media_duration - pos) / 60), pos };
    }
    if (a.start_time && a.stop_time && !a.recording_id) {
      return airProgress(a.start_time, a.stop_time, a.timeshift_seconds || 0);
    }
    return null;
  }

  _updateProgress() {
    if (!this._hass || !this._config || this._hidden("progress")) return;
    const s = this._hass.states[this._ids().player];
    const bar = this.shadowRoot.querySelector(".bar div");
    if (!s || !bar) return;
    const p = this._progress(s);
    if (!p) return;
    bar.style.width = `${p.pct.toFixed(2)}%`;
    const left = this.shadowRoot.querySelector(".left");
    if (left) left.textContent = this._t("left").replace("{min}", p.left);
    const from = this.shadowRoot.querySelector(".from");
    if (from && p.pos != null) from.textContent = clock(p.pos);
  }

  _act(act) {
    const entity_id = this._ids().player;
    const s = this._hass.states[entity_id];
    if (!s) return;
    const mp = (service, data = {}) => this._call(act, "media_player", service, { entity_id, ...data });
    if (act === "power") mp(s.state === "off" ? "turn_on" : "turn_off");
    if (act === "previous") mp("media_previous_track");
    if (act === "next") mp("media_next_track");
    if (act === "play") mp("media_play");
    if (act === "pause") mp("media_pause");
    if (act === "back" || act === "forward") {
      const a = s.attributes;
      const step = act === "back" ? -SEEK_STEP : SEEK_STEP;
      if (this._playing(s).kind === "live") {
        // Live, a seek is a Unix time: the watched moment ± 30 s.
        const watched = Date.now() / 1000 - (a.timeshift_seconds || 0);
        mp("media_seek", { seek_position: watched + step });
        return;
      }
      let pos = Number(a.media_position || 0);
      if (s.state === "playing" && a.media_position_updated_at) {
        pos += (Date.now() - new Date(a.media_position_updated_at).getTime()) / 1000;
      }
      const target = Math.max(0, pos + step);
      mp("media_seek", { seek_position: a.media_duration ? Math.min(target, a.media_duration) : target });
    }
    if (act === "restart") this._call(act, DOMAIN, "restart_program", {});
    if (act === "record") this._call(act, DOMAIN, "create_recording", {});
    if (act === "stop_record") this._call(act, DOMAIN, "stop_recording", {});
  }

  _draw() {
    const { player } = this._ids();
    const s = player ? this._hass.states[player] : null;
    if (!s) {
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}</style><ha-card><div class="empty">${esc(this._t("no_player"))}</div></ha-card>`;
      return;
    }
    if (this._config.mode === "row") this._drawRow(s);
    else this._drawCard(s, player);
  }

  // The one main button a row offers: pause/play where possible, else power.
  _mainButton(s) {
    if (s.state === "paused" && has(s, F.PLAY)) return this._iconButton("play", "mdi:play", this._t("play"), "main");
    if (s.state === "playing" && has(s, F.PAUSE)) return this._iconButton("pause", "mdi:pause", this._t("pause"), "main");
    const off = s.state === "off";
    if (has(s, off ? F.TURN_ON : F.TURN_OFF)) {
      return this._iconButton("power", "mdi:power", this._t(off ? "power_on" : "power_off"), `main ${off ? "" : "on"}`);
    }
    return "";
  }

  _drawRow(s) {
    const a = s.attributes;
    const { off, kind } = this._playing(s);
    const active = channelsOf(s).find((c) => c.id === a.station_id);
    const pic = !off ? (active?.logo && kind === "live" ? active.logo : a.entity_picture) : null;
    const name = off
      ? a.friendly_name || "waipu"
      : [active?.name || a.media_series_title, a.media_title].filter(Boolean).join(" – ") || this._t("unknown_channel");
    const progress = !off && !this._hidden("progress") ? this._progress(s) : null;
    const stateText = this._hass.formatEntityState ? this._hass.formatEntityState(s) : s.state;
    let status = off ? stateText : "";
    if (!off) {
      const marks = [];
      if (kind === "live") marks.push(`<span class="live"><i class="dot"></i>${esc(this._t("live"))}</span>`);
      else if (kind) marks.push(`<span class="kind">${esc(this._t(kind))}</span>`);
      else marks.push(esc(stateText));
      if (progress) marks.push(`<span class="left">${esc(this._t("left").replace("{min}", progress.left))}</span>`);
      if (kind === "live" && this._isRecording(s)) marks.push(`<span class="rec-mark"><ha-icon icon="mdi:record-circle"></ha-icon></span>`);
      status = marks.join(`<span class="sep"></span>`);
    }
    const icon = pic
      ? `<img src="${esc(pic)}" alt="">`
      : `<ha-icon icon="${off ? "mdi:television-off" : "mdi:television-classic"}"></ha-icon>`;
    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${this._rowCss()}</style>
      <ha-card>
        <div class="row ${off ? "off" : ""}" role="button" tabindex="0">
          <div class="icon ${pic ? "pic" : ""}">${icon}</div>
          <div class="text">
            <div class="name">${esc(name)}</div>
            <div class="state">${status}</div>
            ${progress ? `<div class="bar thin"><div style="width:${progress.pct.toFixed(2)}%"></div></div>` : ""}
          </div>
          ${this._mainButton(s)}
        </div>
        ${this._messageHtml()}
      </ha-card>`;
  }

  _rowCss() {
    return `
      .row { display: flex; align-items: center; gap: 10px; min-height: 56px; padding: 0 10px; cursor: pointer;
        box-sizing: border-box; }
      .icon { flex: none; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center;
        justify-content: center; overflow: hidden; color: var(--accent-color); --mdc-icon-size: 22px;
        background: color-mix(in srgb, var(--accent-color) 18%, transparent); }
      .icon img { width: 100%; height: 100%; object-fit: cover; }
      .icon.pic img[src*="station"] { object-fit: contain; padding: 6px; box-sizing: border-box; }
      .off .icon { color: var(--secondary-text-color); background: var(--secondary-background-color); }
      .text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
      .name { font-size: 14px; font-weight: 500; line-height: 20px; color: var(--primary-text-color);
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .state { display: flex; align-items: center; gap: 6px; font-size: 12px; line-height: 16px;
        color: var(--secondary-text-color); overflow: hidden; white-space: nowrap; }
      .state .live { gap: 4px; }
      .state .dot { width: 6px; height: 6px; }
      .sep::before { content: "·"; }
      .kind { font-weight: 600; color: var(--primary-text-color); }
      .bar.thin { height: 3px; margin-top: 3px; }
      .ctl.main { flex: none; width: 36px; height: 36px; border-radius: 50%; color: var(--text-primary-color);
        background: var(--primary-color); --mdc-icon-size: 20px; }
      .ctl.main:not(.on)[data-act="power"] { background: var(--secondary-background-color); color: var(--primary-color); }
      .ctl.main:hover { filter: brightness(1.1); }
    `;
  }

  _drawCard(s, player) {
    const a = s.attributes;
    const { recordings } = this._ids();
    const { off, onDemand, kind } = this._playing(s);
    const showPic = !off && a.entity_picture && !this._hidden("picture");
    const title = off ? this._t("off") : a.media_title || (s.state === "playing" ? this._t("unknown_channel") : this._t("idle"));
    const active = channelsOf(s).find((c) => c.id === a.station_id);
    const channelName = off ? "" : a.media_series_title || active?.name || "";
    const progress = !off && !this._hidden("progress") ? this._progress(s) : null;
    const recording = !off && kind === "live" && recordings && this._isRecording(s);
    const leftText = progress ? this._t("left").replace("{min}", progress.left) : "";

    // Status line: what kind of playback, how far behind live, recording mark.
    const status = [];
    if (!off && kind === "live") status.push(`<span class="live"><i class="dot"></i>${esc(this._t("live"))}</span>`);
    if (!off && kind && kind !== "live") status.push(`<span class="kind">${esc(this._t(kind))}</span>`);
    if (!off && a.timeshift_minutes) status.push(`<span>${esc(this._t("behind").replace("{min}", a.timeshift_minutes))}</span>`);
    if (recording) status.push(`<span class="rec-mark"><ha-icon icon="mdi:record-circle"></ha-icon>${esc(this._t("recording_now"))}</span>`);

    const canPower = has(s, off ? F.TURN_ON : F.TURN_OFF);
    const power = canPower ? this._iconButton("power", "mdi:power", this._t(off ? "power_on" : "power_off"), `power ${off ? "" : "on"}`) : "";

    // The program's slot: air time live, position on demand.
    let slot = "";
    if (progress) {
      const live = kind === "live";
      const from = live ? timeOf(this._hass, a.start_time) : progress.pos != null ? clock(progress.pos) : "";
      const to = live ? timeOf(this._hass, a.stop_time) : a.media_duration ? clock(a.media_duration) : "";
      slot = `<div class="slot">
          <div class="bar"><div style="width:${progress.pct.toFixed(2)}%"></div></div>
          <div class="ends"><span class="from">${esc(from)}</span><span class="left">${esc(leftText)}</span><span>${esc(to)}</span></div>
        </div>`;
    }

    let controls = "";
    if (!off && !this._hidden("controls")) {
      const side = [];
      const main = [];
      if (has(s, F.PREVIOUS)) main.push(this._iconButton("previous", "mdi:skip-previous", this._t("previous")));
      const seekable = has(s, F.SEEK) && (onDemand || kind === "live");
      if (seekable) main.push(this._iconButton("back", "mdi:rewind-30", this._t("back")));
      if (s.state === "paused" && has(s, F.PLAY)) main.push(this._iconButton("play", "mdi:play", this._t("play"), "primary"));
      else if (s.state === "playing" && has(s, F.PAUSE)) main.push(this._iconButton("pause", "mdi:pause", this._t("pause"), "primary"));
      // Live, forward only goes as far as live itself.
      if (seekable && (onDemand || (a.timeshift_seconds || 0) >= SEEK_STEP)) {
        main.push(this._iconButton("forward", "mdi:fast-forward-30", this._t("forward")));
      }
      if (has(s, F.NEXT)) main.push(this._iconButton("next", "mdi:skip-next", this._t("next")));
      if (kind === "live" && a.restart_available) side.push(this._chip("restart", "mdi:restart", this._t("restart")));
      if (kind === "live" && recordings && !this._hidden("record")) {
        if (recording) side.push(this._chip("stop_record", "mdi:stop", this._t("stop_record"), "rec"));
        else if (a.recordable) side.push(this._chip("record", "mdi:record", this._t("record"), "rec"));
      }
      if (main.length || side.length) {
        controls = `<div class="controls">${main.length ? `<div class="main">${main.join("")}</div>` : ""}
          ${side.length ? `<div class="side">${side.join("")}</div>` : ""}</div>`;
      }
    }

    const picker = this._hidden("channels") ? "" : channelSelect(this._hass, player, s);

    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${PICK_CSS}${this._cardCss()}</style>
      <ha-card class="${off ? "off" : ""} ${showPic ? "has-pic" : "no-pic"} ${this._config.mode}">
        ${off && this._hidden("off_hint") ? "" : `<div class="stage">
          ${showPic ? `<div class="pic"><img src="${esc(a.entity_picture)}" alt=""></div>` : ""}
          <div class="caption">
            ${status.length ? `<div class="status">${status.join("")}</div>` : ""}
            <div class="title">${esc(title)}</div>
            ${channelName ? `<div class="channel">${esc(channelName)}</div>` : ""}
            ${!off && a.episode_title ? `<div class="episode">${esc(a.episode_title)}</div>` : ""}
          </div>
          ${power}
        </div>`}
        <div class="body">
          ${slot}
          ${controls}
          ${picker}
          ${this._message ? `<div class="msg" role="alert">${esc(this._message)}</div>` : ""}
        </div>
      </ha-card>`;
  }

  _cardCss() {
    return `
      /* The program picture runs edge to edge and fades into the card; the
         caption sits on its lower edge like a lower third. */
      .stage { position: relative; }
      .pic { position: relative; aspect-ratio: 16 / 9; overflow: hidden; }
      .pic img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .pic::after { content: ""; position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(to bottom, transparent 45%,
          color-mix(in srgb, var(--card-background-color) 80%, transparent) 78%, var(--card-background-color) 100%); }
      .caption { position: relative; z-index: 1; padding: 0 16px 4px; margin-top: -56px;
        display: flex; flex-direction: column; gap: 2px; min-width: 0; }
      .no-pic .caption { margin-top: 0; padding-top: 16px; padding-right: 64px; min-height: 48px; justify-content: center; }
      .status { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin-bottom: 4px;
        font-size: 13px; color: var(--secondary-text-color); }
      .kind { font-weight: 600; color: var(--primary-text-color); }
      .title { font-size: 22px; font-weight: 700; line-height: 1.2; letter-spacing: -0.01em; color: var(--primary-text-color);
        overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-wrap: balance; }
      .off .title { font-size: 18px; font-weight: 500; color: var(--secondary-text-color); }
      .channel { font-size: 15px; font-weight: 500; color: var(--primary-text-color); }
      .episode { font-size: 14px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

      .power { position: absolute; top: 12px; right: 12px; z-index: 2; width: 40px; height: 40px; border-radius: 50%;
        color: var(--secondary-text-color); border: 1px solid var(--divider-color);
        background: color-mix(in srgb, var(--card-background-color) 75%, transparent); backdrop-filter: blur(6px); }
      .power.on { color: var(--primary-color); border-color: color-mix(in srgb, var(--primary-color) 60%, transparent); }
      .power:hover { background: var(--secondary-background-color); }
      .off .power { width: 48px; height: 48px; top: 8px; color: var(--primary-color); border-color: var(--primary-color); --mdc-icon-size: 26px; }

      .body { padding: 8px 16px 16px; display: flex; flex-direction: column; gap: 14px; }
      .body:first-child { padding-top: 16px; }
      .body .msg { padding: 0; }
      .slot { display: flex; flex-direction: column; gap: 6px; }
      .ends { display: grid; grid-template-columns: 1fr auto 1fr; font-size: 12px; color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums; }
      .ends span:last-child { text-align: right; }

      .controls { display: flex; flex-direction: column; align-items: center; gap: 12px; }
      .main { display: flex; align-items: center; justify-content: center; gap: 6px; }
      .ctl { width: 44px; height: 44px; border-radius: 50%; color: var(--primary-text-color); --mdc-icon-size: 26px; }
      .ctl:hover { background: var(--secondary-background-color); color: var(--primary-color); }
      .ctl.primary { width: 56px; height: 56px; margin: 0 6px; background: var(--primary-color); color: var(--text-primary-color);
        --mdc-icon-size: 30px; }
      .ctl.primary:hover { background: var(--primary-color); filter: brightness(1.12); color: var(--text-primary-color); }
      .side { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }

      /* Wide: picture on the left, fading to the right; text beside it. */
      @container (min-width: 560px) {
        .full.has-pic .stage { display: grid; grid-template-columns: 50% 1fr; align-items: center; }
        .full.has-pic .pic { grid-area: 1 / 1 / 2 / 3; width: 64%; }
        .full.has-pic .pic::after { background: linear-gradient(to right, transparent 40%,
          color-mix(in srgb, var(--card-background-color) 80%, transparent) 72%, var(--card-background-color) 100%); }
        .full.has-pic .caption { grid-area: 1 / 2; margin-top: 0; padding: 16px 64px 16px 8px; }
        .full .title { font-size: 24px; }
      }
      /* Compact: a small picture beside the text instead of the big one. */
      .compact .stage { display: grid; grid-template-columns: 112px minmax(0, 1fr) auto; gap: 12px; align-items: center;
        padding: 12px 12px 0; }
      .compact.no-pic .stage { grid-template-columns: minmax(0, 1fr) auto; }
      .compact .pic { border-radius: 8px; }
      .compact .pic::after { display: none; }
      .compact .caption, .compact.no-pic .caption { margin: 0; padding: 0; min-height: 0; }
      .compact .status { margin-bottom: 0; font-size: 12px; }
      .compact .title { font-size: 16px; -webkit-line-clamp: 1; }
      .compact .channel { font-size: 13px; color: var(--secondary-text-color); }
      .compact .episode { display: none; }
      .compact .power, .compact.off .power { position: static; width: 40px; height: 40px; --mdc-icon-size: 22px; }
      .compact .body { padding: 10px 12px 12px; gap: 10px; }
      .compact .body:first-child { padding-top: 12px; }
      @container (max-width: 340px) {
        .title { font-size: 19px; }
        .ctl { width: 40px; height: 40px; }
        .ctl.primary { width: 50px; height: 50px; }
        .body { padding: 6px 12px 12px; }
        .caption { padding-left: 12px; padding-right: 12px; }
      }
    `;
  }
}

// --- channels: what's on now and next ----------------------------------------
class WaipuChannelsCard extends WaipuBase {
  constructor() {
    super();
    this._open = null;
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "name", selector: { text: {} } },
        { name: "channels", selector: { text: { multiple: true } } },
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (config.channels && !Array.isArray(config.channels)) throw new Error("channels must be a list");
    this._config = { ...config };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  connectedCallback() {
    // Remaining minutes and bars move with the clock.
    this._tick = setInterval(() => this._render(true), 60000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  _signature() {
    const ids = findEntities(this._hass, this._config);
    const s = this._hass.states[ids.player];
    const progs = Object.entries(ids.programs).map(([sid, p]) => [sid, p.now?.last_updated, p.next?.last_updated]);
    const rem = ids.reminders ? this._hass.states[ids.reminders]?.last_updated : null;
    const r = ids.recordings ? this._hass.states[ids.recordings]?.last_updated : null;
    return [s?.attributes?.channels, s?.attributes?.station_id, s?.state, progs, r, rem, this._open, this._config];
  }

  _rows() {
    const ids = findEntities(this._hass, this._config);
    const s = this._hass.states[ids.player];
    const only = this._config.channels?.length ? new Set(this._config.channels) : null;
    return channelsOf(s)
      .filter((c) => !only || only.has(c.id))
      .map((c) => ({ ...c, now: ids.programs[c.id]?.now, next: ids.programs[c.id]?.next }))
      .filter((c) => c.now);
  }

  _act(act, data) {
    const ids = findEntities(this._hass, this._config);
    const id = data.id;
    const row = this._rows().find((r) => r.id === id);
    if (act === "toggle") {
      this._open = this._open === id ? null : id;
      this._render(true);
      return;
    }
    if (act === "tune") {
      this._call(act + id, "media_player", "play_media", {
        entity_id: ids.player, media_content_type: "channel", media_content_id: id,
      });
    }
    if (act === "record" && row) {
      this._call(act + id, DOMAIN, "create_recording", { station_id: id, program_id: row.now.attributes.program_id });
    }
    if (act === "stop_record") this._call(act + id, DOMAIN, "stop_recording", { recording_id: data.rec });
    if (act === "record_next" && row?.next) {
      this._call(act + id, DOMAIN, "create_recording", { station_id: id, program_id: row.next.attributes.program_id });
    }
    if (act === "record_series" && row) {
      this._call(act + id, DOMAIN, "create_serial_recording", { station_id: id, program_id: row.now.attributes.program_id });
    }
    if (act === "details" && row) {
      this._call(act + id, DOMAIN, "open_program_on_android_tv", { station_id: id, program_id: row.now.attributes.program_id });
    }
    if (act === "remind_next" && row?.next) {
      this._call(act + id, DOMAIN, "add_reminder", { station_id: id, program_id: row.next.attributes.program_id });
    }
    if (act === "remind_remove" && row?.next) {
      const r = reminderFor(remindersOf(this._hass, ids.reminders), id, this._nextProgram(row));
      if (r) this._call(act + id, DOMAIN, "remove_reminder", { reminder_id: r.id });
    }
  }

  // The next program as reminderFor() wants it.
  _nextProgram(row) {
    const a = row.next.attributes;
    return { id: a.program_id, series_id: a.series_id };
  }

  _draw() {
    const hass = this._hass;
    const ids = findEntities(hass, this._config);
    const player = hass.states[ids.player];
    const rem = remindersOf(hass, ids.reminders);
    const rows = this._rows();
    const tuned = player && player.state !== "off" ? player.attributes.station_id : null;
    const running = new Map(
      recordingsOf(hass, ids.recordings).filter((r) => r.status === "RECORDING").map((r) => [r.station_id, r.recording_id])
    );
    const dvr = Boolean(ids.recordings);
    const head = this._config.name === "" ? "" : `<div class="head">${esc(this._config.name || this._t("channels_title"))}</div>`;
    if (!rows.length) {
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this._css()}</style><ha-card>${head}<div class="empty">${esc(this._t(player ? "no_channels" : "no_player"))}</div></ha-card>`;
      return;
    }
    const items = rows.map((c) => {
      const now = c.now.attributes;
      const p = airProgress(now.start_time, now.stop_time);
      const open = this._open === c.id;
      const rec = running.get(c.id);
      const canRecord = dvr && !now.recording_forbidden;
      const logo = c.logo ? `<img src="${esc(c.logo)}" alt="">` : `<span>${esc(c.name)}</span>`;
      // A two-parter repeats its title: then the episode says more.
      const nextTitle = c.next && c.next.state === c.now.state && c.next.attributes.episode_title
        ? c.next.attributes.episode_title : c.next?.state;
      const next = c.next ? `<div class="next"><span class="t">${esc(timeOf(hass, c.next.attributes.start_time))}</span>${esc(nextTitle)}</div>` : "";
      // Red in the row only while recording; recording itself is in the menu.
      const recBtn = rec
        ? this._iconButton("stop_record", "mdi:stop-circle-outline", this._t("stop_record"), "rec", c.id).replace("data-act", `data-rec="${esc(rec)}" data-act`)
        : "";
      const extra = open
        ? `<div class="extra">
            ${now.description ? `<p>${esc(now.description)}</p>` : ""}
            <div class="chips">
              ${canRecord && !rec ? this._chip("record", "mdi:record", this._t("record_now"), "rec", c.id) : ""}
              ${c.next && canRecord ? this._chip("record_next", "mdi:record", this._t("record_next"), "rec", c.id) : ""}
              ${now.series_id && canRecord ? this._chip("record_series", "mdi:record-rec", this._t("record_series"), "rec", c.id) : ""}
              ${c.next && ids.reminders
                ? reminderFor(rem, c.id, this._nextProgram(c))
                  ? this._chip("remind_remove", "mdi:bell-off-outline", this._t("remind_remove"), "", c.id)
                  : this._chip("remind_next", "mdi:bell-outline", this._t("remind_next"), "", c.id)
                : ""}
              ${player?.attributes?.target_android_tv ? this._chip("details", "mdi:information-outline", this._t("details_tv"), "", c.id) : ""}
            </div>
          </div>`
        : "";
      return `
        <div class="item ${tuned === c.id ? "tuned" : ""} ${open ? "open" : ""}">
          <button class="main-tap ${this._bz("tune" + c.id)}" data-act="tune" data-id="${esc(c.id)}"
            aria-label="${esc(this._t("watch"))}: ${esc(c.name)}">
            <div class="logo">${logo}${tuned === c.id ? "" : `<span class="go" title="${esc(this._t("switch_here"))}"><ha-icon icon="mdi:play"></ha-icon></span>`}</div>
            <div class="info">
              <div class="now">${rec ? `<span class="rec-mark"><ha-icon icon="mdi:record-circle"></ha-icon></span>` : ""}<span class="nt">${esc(c.now.state)}</span></div>
              ${p ? `<div class="bar"><div style="width:${p.pct.toFixed(1)}%"></div></div>` : ""}
              <div class="meta">
                <span>${esc(tuned === c.id ? this._t("tuned") : c.name)}</span>
                ${p ? `<span>${esc(this._t("left").replace("{min}", p.left))}</span>` : ""}
              </div>
              ${next}
            </div>
          </button>
          <div class="acts">
            ${recBtn}
            ${this._iconButton("toggle", open ? "mdi:chevron-up" : "mdi:chevron-down", this._t("more"), "", c.id)}
          </div>
          ${extra}
        </div>`;
    });
    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${this._css()}</style>
      <ha-card>${head}<div class="list">${items.join("")}</div>${this._messageHtml()}</ha-card>`;
  }

  _css() {
    return `
      .head { padding: 14px 16px 6px; font-size: 16px; font-weight: 600; color: var(--primary-text-color); }
      .list { display: flex; flex-direction: column; padding: 4px 8px 8px; }
      .item { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; border-radius: 12px;
        border-left: 3px solid transparent; }
      .item + .item { border-top: 1px solid var(--divider-color); }
      .item.tuned { border-left-color: var(--accent-color);
        background: color-mix(in srgb, var(--accent-color) 7%, transparent); }
      .main-tap { display: grid; grid-template-columns: 64px minmax(0, 1fr); gap: 12px; align-items: center;
        padding: 10px 6px 10px 8px; text-align: left; justify-content: stretch; border-radius: 12px; }
      .main-tap:hover { background: var(--secondary-background-color); }
      .logo { position: relative; width: 64px; height: 36px; border-radius: 6px; display: flex; align-items: center; justify-content: center;
        background: var(--secondary-background-color); font-size: 11px; color: var(--secondary-text-color); }
      /* Tapping the row switches over: a play badge says so. */
      .go { position: absolute; right: -6px; bottom: -6px; width: 20px; height: 20px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; background: var(--primary-color);
        color: var(--text-primary-color); --mdc-icon-size: 14px; box-shadow: 0 0 0 2px var(--card-background-color); }
      .logo img { width: 100%; height: 100%; object-fit: contain; padding: 4px; box-sizing: border-box; }
      .info { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
      .now { font-size: 15px; font-weight: 600; color: var(--primary-text-color); display: flex; align-items: center; gap: 4px;
        min-width: 0; }
      .now .nt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .now .rec-mark { flex: none; }
      .info .bar { height: 3px; }
      .meta { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--secondary-text-color); }
      .tuned .meta span:first-child { color: var(--accent-color); font-weight: 600; }
      .next { font-size: 12px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .next .t { font-variant-numeric: tabular-nums; margin-right: 6px; color: var(--primary-text-color); }
      .acts { display: flex; align-items: center; gap: 2px; padding-right: 4px; }
      .ctl { width: 40px; height: 40px; border-radius: 50%; color: var(--secondary-text-color); --mdc-icon-size: 22px; }
      .ctl:hover { background: var(--secondary-background-color); color: var(--primary-color); }
      .ctl.rec { color: var(--error-color); }
      .extra { grid-column: 1 / -1; padding: 0 12px 12px; }
      .extra .chips { display: grid; grid-template-columns: repeat(auto-fill, minmax(148px, 1fr)); gap: 8px; }
      .extra .chip { height: 34px; font-size: 13px; min-width: 0; }
      .extra .chip span { overflow: hidden; text-overflow: ellipsis; }
      .extra p { margin: 0 0 10px; font-size: 13px; line-height: 1.45; color: var(--secondary-text-color);
        display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
      .chips { display: flex; flex-wrap: wrap; gap: 8px; }
      @container (max-width: 380px) {
        .main-tap { grid-template-columns: 48px minmax(0, 1fr); gap: 10px; }
        .logo { width: 48px; height: 28px; }
        .extra { padding-left: 12px; }
      }
    `;
  }
}

// --- recordings ---------------------------------------------------------------
const TABS = ["new", "available", "planned"];

class WaipuRecordingsCard extends WaipuBase {
  constructor() {
    super();
    this._tab = null;
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "name", selector: { text: {} } },
        {
          name: "tab",
          selector: { select: { mode: "dropdown", options: TABS.map((k) => ({ value: k, label: uiText(`tab_${k}`) })) } },
        },
        { name: "max", selector: { number: { min: 1, max: 100, mode: "box" } } },
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (config.tab && !TABS.includes(config.tab)) throw new Error("tab must be new, available or planned");
    this._config = { max: 20, ...config };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  _signature() {
    const ids = findEntities(this._hass, this._config);
    const r = ids.recordings ? this._hass.states[ids.recordings] : null;
    const p = this._hass.states[ids.player];
    return [r?.last_updated, p?.attributes?.channels?.length, this._tab, this._config];
  }

  _lists() {
    const ids = findEntities(this._hass, this._config);
    const all = recordingsOf(this._hass, ids.recordings);
    return {
      new: all.filter((r) => r.is_new && (r.status === "FINISHED" || r.status === "RECORDING")),
      available: all.filter((r) => r.status === "FINISHED" || r.status === "RECORDING"),
      // Soonest first.
      planned: all.filter((r) => r.status === "SCHEDULED").sort((a, b) => (a.date || "").localeCompare(b.date || "")),
    };
  }

  _act(act, data) {
    const ids = findEntities(this._hass, this._config);
    const id = data.id;
    if (act === "tab") {
      this._tab = data.tab;
      this._render(true);
      return;
    }
    if (act === "play") {
      this._call(act + id, "media_player", "play_media", {
        entity_id: ids.player, media_content_type: "waipu_recording", media_content_id: id,
      });
    }
    if (act === "stop") this._call(act + id, DOMAIN, "stop_recording", { recording_id: id });
    if (act === "delete" && this._armed("delete" + id)) {
      this._call(act + id, DOMAIN, "delete_recording", { recording_id: id });
    }
  }

  _draw() {
    const hass = this._hass;
    const ids = findEntities(hass, this._config);
    const head = this._config.name === "" ? "" : `<div class="head">${esc(this._config.name || this._t("recordings_title"))}</div>`;
    if (!ids.recordings) {
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this._css()}</style><ha-card>${head}<div class="empty">${esc(this._t("no_dvr"))}</div></ha-card>`;
      return;
    }
    const lists = this._lists();
    const tab = this._tab || this._config.tab || (lists.new.length ? "new" : "available");
    const logos = Object.fromEntries(channelsOf(hass.states[ids.player]).map((c) => [c.id, c]));
    const tabs = TABS.map(
      (t) => `<button class="tab ${t === tab ? "on" : ""}" data-act="tab" data-tab="${t}" role="tab"
        aria-selected="${t === tab}">${esc(this._t(`tab_${t}`))}<span class="n">${lists[t].length}</span></button>`
    ).join("");
    const items = lists[tab].slice(0, this._config.max).map((r) => this._item(r, logos[r.station_id]));
    const body = items.length ? `<div class="list">${items.join("")}</div>` : `<div class="empty">${esc(this._t(`empty_${tab}`))}</div>`;
    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${this._css()}</style>
      <ha-card>${head}<div class="tabs" role="tablist">${tabs}</div>${body}${this._messageHtml()}</ha-card>`;
  }

  _item(r, channel) {
    const hass = this._hass;
    const id = r.recording_id;
    const watchable = r.status === "FINISHED" || r.status === "RECORDING";
    const pct = r.fully_watched ? 100 : r.position_percentage || 0;
    const badges = [];
    if (r.status === "RECORDING") badges.push(`<span class="badge rec"><i class="dot"></i>${esc(this._t("running"))}</span>`);
    else if (r.is_new) badges.push(`<span class="badge new">${esc(this._t("new_badge"))}</span>`);
    else if (r.fully_watched) badges.push(`<span class="badge">${esc(this._t("watched"))}</span>`);
    const thumb = r.image ? `<img src="${esc(r.image)}" alt="">` : `<ha-icon icon="mdi:movie-open-outline"></ha-icon>`;
    const confirmKey = "delete" + id;
    const armed = this._confirm === confirmKey;
    const actions = [];
    if (r.status === "RECORDING") actions.push(this._iconButton("stop", "mdi:stop-circle-outline", this._t("stop_record"), "rec", id));
    actions.push(
      armed
        ? this._chip("delete", "mdi:delete", this._t(r.status === "SCHEDULED" ? "confirm_cancel" : "confirm_delete"), "confirm", id)
        : this._iconButton("delete", r.status === "SCHEDULED" ? "mdi:calendar-remove" : "mdi:delete-outline",
            this._t(r.status === "SCHEDULED" ? "cancel_rec" : "delete"), "", id)
    );
    const main = `
      <div class="thumb">${thumb}${watchable && pct ? `<div class="bar"><div style="width:${pct}%"></div></div>` : ""}
        ${watchable ? `<span class="playmark"><ha-icon icon="mdi:play"></ha-icon></span>` : ""}</div>
      <div class="info">
        <div class="title">${esc(r.title)}</div>
        ${r.episode_title ? `<div class="ep">${esc(r.episode_title)}</div>` : ""}
        <div class="meta">${badges.join("")}<span>${esc(dayTimeOf(hass, r.date))}</span>${channel ? `<span>${esc(channel.name)}</span>` : ""}</div>
      </div>`;
    return `
      <div class="item">
        ${watchable
          ? `<button class="main-tap ${this._bz("play" + id)}" data-act="play" data-id="${esc(id)}" aria-label="${esc(this._t("play_tv"))}: ${esc(r.title)}">${main}</button>`
          : `<div class="main-tap static">${main}</div>`}
        <div class="acts">${actions.join("")}</div>
      </div>`;
  }

  _css() {
    return `
      .head { padding: 14px 16px 6px; font-size: 16px; font-weight: 600; color: var(--primary-text-color); }
      .tabs { display: flex; gap: 6px; padding: 6px 12px 4px; flex-wrap: wrap; }
      .tab { gap: 6px; height: 34px; padding: 0 12px; border-radius: 17px; font-size: 14px; font-weight: 500;
        color: var(--secondary-text-color); border: 1px solid var(--divider-color); }
      .tab:hover { color: var(--primary-color); border-color: var(--primary-color); }
      .tab.on { background: var(--primary-color); color: var(--text-primary-color); border-color: var(--primary-color); }
      .tab .n { font-size: 12px; font-variant-numeric: tabular-nums; opacity: .8; }
      .list { display: flex; flex-direction: column; padding: 6px 8px 8px; }
      .item { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; border-radius: 12px; }
      .item + .item { border-top: 1px solid var(--divider-color); }
      .main-tap { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 12px; align-items: center;
        padding: 8px; text-align: left; justify-content: stretch; border-radius: 12px; }
      button.main-tap:hover { background: var(--secondary-background-color); }
      .thumb { position: relative; aspect-ratio: 16 / 9; border-radius: 8px; overflow: hidden;
        background: var(--secondary-background-color); display: flex; align-items: center; justify-content: center;
        color: var(--secondary-text-color); }
      .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .thumb .bar { position: absolute; left: 0; right: 0; bottom: 0; height: 3px; border-radius: 0; }
      .playmark { position: absolute; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
        justify-content: center; background: color-mix(in srgb, var(--card-background-color) 70%, transparent);
        color: var(--primary-color); --mdc-icon-size: 20px; }
      button.main-tap:hover .playmark { background: var(--primary-color); color: var(--text-primary-color); }
      .info { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
      .title { font-size: 15px; font-weight: 600; color: var(--primary-text-color); overflow: hidden;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
      .ep { font-size: 13px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .meta { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; font-size: 12px; color: var(--secondary-text-color); }
      .badge { font-size: 11px; font-weight: 600; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--divider-color); }
      .badge.new { border-color: var(--accent-color); color: var(--accent-color); }
      .badge.rec { display: inline-flex; align-items: center; gap: 4px; border-color: var(--error-color); color: var(--error-color); }
      .badge .dot { width: 6px; height: 6px; }
      .acts { display: flex; align-items: center; gap: 4px; padding-right: 6px; }
      .ctl { width: 40px; height: 40px; border-radius: 50%; color: var(--secondary-text-color); --mdc-icon-size: 22px; }
      .ctl:hover { background: var(--secondary-background-color); color: var(--error-color); }
      .ctl.rec { color: var(--error-color); }
      @container (max-width: 400px) {
        .main-tap { grid-template-columns: 88px minmax(0, 1fr); gap: 10px; }
      }
    `;
  }
}

// --- guide: the program as a timeline ------------------------------------------
const GUIDE_PX_PER_MIN = 4;
const GUIDE_REFRESH_MS = 5 * 60000;

class WaipuGuideCard extends WaipuBase {
  constructor() {
    super();
    this._guide = null;
    this._selected = null;
    this._scrolled = false;
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "name", selector: { text: {} } },
        { name: "channels", selector: { text: { multiple: true } } },
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (config.channels && !Array.isArray(config.channels)) throw new Error("channels must be a list");
    this._config = { ...config };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return 8;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    // Reload when a recording changed (planned marks) — or the first time.
    const ids = findEntities(hass, this._config);
    const rec = ids.recordings ? hass.states[ids.recordings]?.last_updated : null;
    if (first || rec !== this._recStamp) {
      this._recStamp = rec;
      this._load();
    }
    this._render();
  }

  connectedCallback() {
    this._timer = setInterval(() => this._load(), GUIDE_REFRESH_MS);
    if (this._hass) this._load();
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    this._resize?.disconnect();
  }

  async _load() {
    if (!this._hass?.connection) return;
    try {
      this._guide = await this._hass.connection.sendMessagePromise({ type: "waipu/guide" });
      this._error = null;
    } catch (err) {
      this._error = err?.message || String(err);
    }
    this._render(true);
  }

  _signature() {
    const ids = findEntities(this._hass, this._config);
    const p = this._hass.states[ids.player];
    const rem = ids.reminders ? this._hass.states[ids.reminders]?.last_updated : null;
    return [this._guide?.now, this._guide?.stations?.length, this._error, this._selected,
      p?.attributes?.station_id, p?.state, rem, this._config];
  }

  _find(sid, pid) {
    const st = this._guide?.stations?.find((s) => s.id === sid);
    return { st, p: st?.programs.find((x) => x.id === pid) };
  }

  _act(act, data) {
    const ids = findEntities(this._hass, this._config);
    if (act === "select") {
      const key = `${data.sid}/${data.pid}`;
      this._selected = this._selected === key ? null : key;
      this._reveal = Boolean(this._selected);
      this._render(true);
      return;
    }
    if (act === "close") {
      this._selected = null;
      this._render(true);
      return;
    }
    if (!this._selected) return;
    const [sid, pid] = this._selected.split("/");
    const { p } = this._find(sid, pid);
    const done = () => this._load();
    if (act === "watch") {
      this._call(act, "media_player", "play_media", {
        entity_id: ids.player, media_content_type: "waipu_program", media_content_id: `${sid}/${pid}`,
      });
    }
    if (act === "details") this._call(act, DOMAIN, "open_program_on_android_tv", { station_id: sid, program_id: pid });
    if (act === "record") this._call(act, DOMAIN, "create_recording", { station_id: sid, program_id: pid }).then(done);
    if (act === "record_series") this._call(act, DOMAIN, "create_serial_recording", { station_id: sid, program_id: pid }).then(done);
    if (act === "cancel" && p?.recording_id && this._armed("cancel")) {
      this._call(act, DOMAIN, "delete_recording", { recording_id: p.recording_id }).then(done);
    }
    if (act === "remind") this._call(act, DOMAIN, "add_reminder", { station_id: sid, program_id: pid });
    if (act === "remind_series") this._call(act, DOMAIN, "add_reminder", { station_id: sid, program_id: pid, series: true });
    if (act === "remind_remove") {
      const r = reminderFor(remindersOf(this._hass, ids.reminders), sid, p || {});
      if (r) this._call(act, DOMAIN, "remove_reminder", { reminder_id: r.id });
    }
  }

  _draw() {
    const hass = this._hass;
    const head = this._config.name === "" ? "" : `<div class="head">${esc(this._config.name || this._t("guide_title"))}</div>`;
    if (!this._guide) {
      const text = this._error ? this._t("failed").replace("{error}", this._error) : this._t("loading");
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this._css()}</style><ha-card>${head}<div class="empty">${esc(text)}</div></ha-card>`;
      return;
    }
    const g = this._guide;
    const ids = findEntities(hass, this._config);
    const player = hass.states[ids.player];
    const tuned = player && player.state !== "off" ? player.attributes.station_id : null;
    const only = this._config.channels?.length ? new Set(this._config.channels) : null;
    const stations = g.stations.filter((s) => !only || only.has(s.id));
    // The timeline starts on the half hour before the window's start.
    const start = new Date(g.start);
    start.setMinutes(start.getMinutes() < 30 ? 0 : 30, 0, 0);
    const end = new Date(g.end).getTime();
    const minutes = Math.ceil((end - start.getTime()) / 60000);
    const width = minutes * GUIDE_PX_PER_MIN;
    const x = (iso) => Math.max(0, ((new Date(iso).getTime() - start.getTime()) / 60000) * GUIDE_PX_PER_MIN);
    const nowX = x(new Date().toISOString());

    const marks = [];
    // The first mark would sit half under the channel column.
    for (let m = 30; m <= minutes; m += 30) {
      const t = new Date(start.getTime() + m * 60000);
      marks.push(`<span class="mark ${m % 60 ? "half" : ""}" style="left:${m * GUIDE_PX_PER_MIN}px">${esc(timeOf(hass, t.toISOString()))}</span>`);
    }
    const rem = remindersOf(hass, ids.reminders);
    const rows = stations.map((s) => {
      const blocks = s.programs.map((p) => {
        const left = x(p.start);
        const w = Math.max(x(p.stop) - left, 2);
        const now = new Date(p.start) <= new Date() && new Date() < new Date(p.stop);
        const past = new Date(p.stop) <= new Date();
        const key = `${s.id}/${p.id}`;
        return `<button class="prog ${now ? "now" : ""} ${past ? "past" : ""} ${this._selected === key ? "sel" : ""}"
          style="left:${left}px;width:${w - 2}px" data-act="select" data-sid="${esc(s.id)}" data-pid="${esc(p.id)}"
          title="${esc(p.title)}">
          ${p.recording ? `<i class="recdot ${p.recording === "RECORDING" ? "on" : ""}"></i>` : ""}
          ${reminderFor(rem, s.id, p) ? `<ha-icon class="bell" icon="mdi:bell-ring-outline"></ha-icon>` : ""}
          <span class="pt">${esc(p.title)}</span><span class="ps">${esc(timeOf(hass, p.start))}</span></button>`;
      });
      const logo = s.logo ? `<img src="${esc(s.logo)}" alt="${esc(s.name)}">` : `<span>${esc(s.name)}</span>`;
      // The details open right under their channel and push the rest down.
      const open = this._selected?.startsWith(`${s.id}/`) ? `<div class="dslot">${this._detail(g)}</div>` : "";
      return `<div class="grow ${tuned === s.id ? "tuned" : ""}"><div class="ch" title="${esc(s.name)}">${logo}</div>
        <div class="lane" style="width:${width}px">${blocks.join("")}</div></div>${open}`;
    });

    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${this._css()}</style>
      <ha-card>${head}
        <div class="scroller">
          <div class="grid" style="width:${width + 72}px">
            <div class="timeline"><div class="corner"></div><div class="scale" style="width:${width}px">${marks.join("")}<i class="nowdot" style="left:${nowX}px"></i></div></div>
            ${rows.join("")}
            <div class="nowline" style="left:${72 + nowX}px" aria-label="${esc(this._t("now_line"))}"></div>
          </div>
        </div>
        ${this._messageHtml()}
      </ha-card>`;
    // Open on "now" once the card has a width; afterwards keep where the
    // user scrolled.
    const sc = this.shadowRoot.querySelector(".scroller");
    const place = () => {
      if (this._scrolled) {
        sc.scrollLeft = this._scrollLeft || 0;
        sc.scrollTop = this._scrollTop || 0;
      } else if (sc.clientWidth) {
        sc.scrollLeft = Math.max(0, nowX - 60);
        this._scrolled = true;
      } else {
        requestAnimationFrame(place);
      }
    };
    place();
    sc.addEventListener("scroll", () => {
      if (!this._scrolled) return;
      this._scrollLeft = sc.scrollLeft;
      this._scrollTop = sc.scrollTop;
    });
    // The open details stay as wide as the visible part, not the timeline.
    const grid = sc.querySelector(".grid");
    this._resize?.disconnect();
    this._resize = new ResizeObserver(() => grid.style.setProperty("--view-w", `${sc.clientWidth}px`));
    this._resize.observe(sc);
    // Freshly opened details: make sure they're in view.
    if (this._reveal) {
      this._reveal = false;
      const slot = sc.querySelector(".dslot");
      if (slot) {
        const top = slot.offsetTop - 26;
        const bottom = slot.offsetTop + slot.offsetHeight;
        if (bottom > sc.scrollTop + sc.clientHeight) sc.scrollTop = Math.min(top, bottom - sc.clientHeight);
        else if (top < sc.scrollTop) sc.scrollTop = top;
      }
    }
  }

  _detail(g) {
    if (!this._selected) return "";
    const [sid, pid] = this._selected.split("/");
    const { st, p } = this._find(sid, pid);
    if (!p) return "";
    const hass = this._hass;
    const now = new Date(p.start) <= new Date() && new Date() < new Date(p.stop);
    const past = new Date(p.stop) <= new Date();
    const chips = [];
    if (now) chips.push(this._chip("watch", "mdi:play", this._t("watch")));
    const player = this._hass.states[findEntities(this._hass, this._config).player];
    if (player?.attributes?.target_android_tv) chips.push(this._chip("details", "mdi:information-outline", this._t("details_tv")));
    if (g.dvr && p.recordable && !past) {
      if (p.recording === "SCHEDULED") {
        chips.push(this._confirm === "cancel"
          ? this._chip("cancel", "mdi:calendar-remove", this._t("confirm_cancel"), "confirm")
          : this._chip("cancel", "mdi:calendar-remove", this._t("cancel_rec"), "rec"));
      } else if (!p.recording) {
        chips.push(this._chip("record", "mdi:record", this._t("record"), "rec"));
      }
      if (p.series_id && !p.recording) chips.push(this._chip("record_series", "mdi:record-rec", this._t("record_series"), "rec"));
    }
    // Remind (and switch at the start) — only before it starts.
    const ids = findEntities(this._hass, this._config);
    if (ids.reminders && !now && !past) {
      const r = reminderFor(remindersOf(this._hass, ids.reminders), sid, p);
      if (r) chips.push(this._chip("remind_remove", "mdi:bell-off-outline", this._t("remind_remove")));
      else {
        chips.push(this._chip("remind", "mdi:bell-outline", this._t("remind")));
        if (p.series_id) chips.push(this._chip("remind_series", "mdi:bell-ring-outline", this._t("remind_series")));
      }
    }
    const state = p.recording === "RECORDING" ? this._t("recording_now") : p.recording === "SCHEDULED" ? this._t("planned") : "";
    return `
      <div class="detail" role="region">
        <div class="dhead">
          <div>
            <div class="dtitle">${esc(p.title)}</div>
            <div class="dmeta">${esc(st.name)}<span>${esc(timeOf(hass, p.start))}–${esc(timeOf(hass, p.stop))}</span>
              ${state ? `<span class="rec-mark">${esc(state)}</span>` : ""}</div>
            ${p.episode_title ? `<div class="dep">${esc(p.episode_title)}</div>` : ""}
          </div>
          ${this._iconButton("close", "mdi:close", this._t("close"))}
        </div>
        <div class="chips">${chips.join("")}</div>
      </div>`;
  }

  _css() {
    return `
      .head { padding: 14px 16px 6px; font-size: 16px; font-weight: 600; color: var(--primary-text-color); }
      /* Scrolls inside the card, so the times and channels always stay in view. */
      .scroller { overflow: auto; max-height: var(--waipu-guide-height, 70vh); overscroll-behavior: contain;
        scrollbar-width: thin; }
      .grid { position: relative; padding-bottom: 6px; }
      .timeline { display: flex; position: sticky; top: 0; z-index: 4; height: 26px; background: var(--card-background-color);
        border-bottom: 1px solid var(--divider-color); }
      .corner { width: 72px; flex: none; position: sticky; left: 0; z-index: 5; background: var(--card-background-color); }
      .scale { position: relative; height: 26px; }
      .mark { position: absolute; top: 4px; transform: translateX(-50%); font-size: 12px; color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums; }
      .mark.half { color: color-mix(in srgb, var(--secondary-text-color) 60%, transparent); }
      .grow { display: flex; height: 52px; }
      .grow + .grow { border-top: 1px solid var(--divider-color); }
      .ch { width: 72px; flex: none; position: sticky; left: 0; z-index: 2; display: flex; align-items: center;
        justify-content: center; background: var(--card-background-color); border-right: 1px solid var(--divider-color);
        font-size: 11px; color: var(--secondary-text-color); padding: 0 6px; box-sizing: border-box; }
      .ch img { width: 100%; height: 30px; object-fit: contain; }
      .tuned .ch { box-shadow: inset 3px 0 0 var(--accent-color); }
      .lane { position: relative; flex: none; }
      .prog { position: absolute; top: 4px; bottom: 4px; border-radius: 8px; padding: 4px 8px; flex-direction: column;
        align-items: flex-start; justify-content: center; gap: 1px; overflow: hidden; text-align: left;
        background: var(--secondary-background-color); color: var(--primary-text-color); }
      .prog:hover { box-shadow: inset 0 0 0 1px var(--primary-color); }
      .prog.now { background: color-mix(in srgb, var(--accent-color) 38%, var(--secondary-background-color));
        box-shadow: inset 3px 0 0 var(--accent-color); }
      .prog.past { opacity: .5; }
      .prog.sel { box-shadow: inset 0 0 0 2px var(--primary-color); }
      .pt { font-size: 13px; font-weight: 600; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .ps { font-size: 11px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
      .bell { position: absolute; bottom: 4px; right: 5px; --mdc-icon-size: 14px; color: var(--primary-color); }
      .recdot { position: absolute; top: 6px; right: 6px; width: 8px; height: 8px; border-radius: 50%;
        border: 2px solid var(--error-color); box-sizing: border-box; }
      .recdot.on { background: var(--error-color); }
      .nowdot { position: absolute; bottom: -4px; left: 0; width: 8px; height: 8px; margin-left: -3px; border-radius: 50%;
        background: var(--error-color); }
      .nowline { position: absolute; top: 22px; bottom: 0; width: 2px; background: var(--error-color); z-index: 1;
        pointer-events: none; }
      .dslot { position: sticky; left: 0; z-index: 3; width: var(--view-w, 100%); box-sizing: border-box;
        padding: 2px 12px 10px; background: var(--card-background-color); border-top: 1px solid var(--divider-color); }
      .detail { padding: 12px; border-radius: 12px; background: var(--secondary-background-color); }
      .dhead { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
      .dtitle { font-size: 16px; font-weight: 700; color: var(--primary-text-color); }
      .dmeta { display: flex; flex-wrap: wrap; gap: 4px 10px; font-size: 13px; color: var(--secondary-text-color); margin-top: 2px; }
      .dep { font-size: 13px; color: var(--secondary-text-color); margin-top: 2px; }
      .detail .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
      .ctl { width: 36px; height: 36px; border-radius: 50%; color: var(--secondary-text-color); flex: none; }
      .ctl:hover { background: var(--card-background-color); color: var(--primary-color); }
    `;
  }
}

// --- reminders: remind and switch at the start ---------------------------------
const WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

class WaipuRemindersCard extends WaipuBase {
  constructor() {
    super();
    this._open = null;
    this._form = null;
    // The schedule form keeps its own values while typing.
    this.shadowRoot.addEventListener("input", (e) => {
      const el = e.target.closest("[data-field]");
      if (!el || !this._form) return;
      this._form[el.dataset.field] = el.type === "checkbox" ? el.checked : el.value;
    });
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "name", selector: { text: {} } },
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = { ...config };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  connectedCallback() {
    // "today"/"tomorrow" move with the clock.
    this._tick = setInterval(() => this._render(true), 60000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  _signature() {
    const ids = findEntities(this._hass, this._config);
    const r = ids.reminders ? this._hass.states[ids.reminders] : null;
    return [r?.last_updated, this._open, this._form, this._config];
  }

  _act(act, data) {
    const id = data.id;
    if (act === "toggle_open") {
      this._open = this._open === id ? null : id;
      this._render(true);
      return;
    }
    if (act === "enabled") this._call(act + id, DOMAIN, "update_reminder", { reminder_id: id, enabled: data.on !== "1" });
    if (act === "switch") this._call(act + id, DOMAIN, "update_reminder", { reminder_id: id, switch: data.on !== "1" });
    if (act === "skip") this._call(act + id, DOMAIN, "update_reminder", { reminder_id: id, skip_next: data.on !== "1" });
    if (act === "delete" && this._armed("delete" + id)) {
      this._call(act + id, DOMAIN, "remove_reminder", { reminder_id: id });
    }
    if (act === "new") {
      const player = this._hass.states[findEntities(this._hass, this._config).player];
      this._form = { time: "20:15", days: [...WEEKDAY_KEYS], station_id: channelsOf(player)[0]?.id || "", once: false, switch: true };
      this._render(true);
    }
    if (act === "day" && this._form) {
      const days = new Set(this._form.days);
      days.has(data.day) ? days.delete(data.day) : days.add(data.day);
      this._form = { ...this._form, days: WEEKDAY_KEYS.filter((d) => days.has(d)) };
      this._render(true);
    }
    if (act === "form_cancel") {
      this._form = null;
      this._render(true);
    }
    if (act === "form_save" && this._form?.station_id && this._form.time && this._form.days.length) {
      const f = this._form;
      this._call(act, DOMAIN, "add_reminder", {
        station_id: f.station_id, time: f.time, days: f.days, once: f.once, switch: f.switch,
      }).then(() => {
        if (!this._message) this._form = null;
        this._render(true);
      });
    }
  }

  // "today", "tomorrow" or "Fri 21.11."
  _when(iso) {
    const d = new Date(iso);
    const day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
    const diff = Math.round((day(d) - day(new Date())) / 86400000);
    if (diff === 0) return this._t("today");
    if (diff === 1) return this._t("tomorrow");
    return d.toLocaleDateString(lang(this._hass), { weekday: "short", day: "2-digit", month: "2-digit" });
  }

  _dayName(key) {
    // 1 Jan 2024 was a Monday.
    return new Date(2024, 0, 1 + WEEKDAY_KEYS.indexOf(key)).toLocaleDateString(lang(this._hass), { weekday: "short" });
  }

  _repeat(r) {
    if (r.kind === "program") return this._t("kind_program");
    if (r.kind === "series") return this._t("kind_series");
    const days = r.days || WEEKDAY_KEYS;
    let text;
    if (days.length === 7) text = this._t("daily");
    else if (days.join() === "mon,tue,wed,thu,fri") text = this._t("weekdays");
    else if (days.join() === "sat,sun") text = this._t("weekend");
    else text = days.map((d) => this._dayName(d)).join(", ");
    return r.once ? `${text}, ${this._t("once")}` : text;
  }

  _draw() {
    const hass = this._hass;
    const ids = findEntities(hass, this._config);
    const head = this._config.name === "" ? "" : `<div class="head">${esc(this._config.name || this._t("reminders_title"))}</div>`;
    if (!ids.reminders) {
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this._css()}</style><ha-card>${head}<div class="empty">${esc(this._t("no_player"))}</div></ha-card>`;
      return;
    }
    const rem = remindersOf(hass, ids.reminders);
    const next = Object.fromEntries(rem.upcoming.slice().reverse().map((o) => [o.reminder_id, o]));
    // Coming first, switched-off ones last.
    const list = rem.list.slice().sort((a, b) => {
      const ka = a.next ? Date.parse(a.next) : Infinity;
      const kb = b.next ? Date.parse(b.next) : Infinity;
      return ka === kb ? 0 : ka < kb ? -1 : 1;
    });
    const items = list.map((r) => this._item(r, next[r.id]));
    const body = items.length ? `<div class="list">${items.join("")}</div>` : `<div class="empty">${esc(this._t("no_reminders"))}</div>`;
    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${PICK_CSS}${this._css()}</style>
      <ha-card>${head}${body}
        ${this._form ? this._formHtml() : `<div class="foot">${this._chip("new", "mdi:plus", this._t("add_schedule"))}</div>`}
        ${this._messageHtml()}
      </ha-card>`;
  }

  _item(r, occ) {
    const hass = this._hass;
    const on = r.enabled !== false;
    const id = r.id;
    const time = occ ? timeOf(hass, occ.start) : r.time || (r.start ? timeOf(hass, r.start) : "");
    // Big time on the left, when underneath; the sentence says what happens.
    const when = !on ? this._t("off_short") : occ ? this._when(occ.start) : "";
    const line = this._t(r.switch ? "switches_to" : "reminds_of").replace("{station}", r.station);
    const title = occ?.title || r.title;
    const meta = [this._repeat(r)];
    if (occ?.skipped) meta.push(this._t("skipped"));
    const open = this._open === id;
    const toggle = `<button class="tgl ${on ? "on" : ""} ${this._bz("enabled" + id)}" role="switch" aria-checked="${on}"
      aria-label="${esc(this._t("reminder_on"))}" data-act="enabled" data-id="${esc(id)}" data-on="${on ? 1 : 0}"><span></span></button>`;
    const armed = this._confirm === "delete" + id;
    const extra = open
      ? `<div class="extra">
          <button class="chip ${r.switch ? "sel" : ""} ${this._bz("switch" + id)}" data-act="switch" data-id="${esc(id)}" data-on="${r.switch ? 1 : 0}"
            role="switch" aria-checked="${!!r.switch}"><ha-icon icon="${r.switch ? "mdi:checkbox-marked-outline" : "mdi:checkbox-blank-outline"}"></ha-icon><span>${esc(this._t("switch_at_start"))}</span></button>
          ${on && occ && r.kind !== "program" ? `<button class="chip ${this._bz("skip" + id)}" data-act="skip" data-id="${esc(id)}" data-on="${occ.skipped ? 1 : 0}">
            <ha-icon icon="${occ.skipped ? "mdi:undo" : "mdi:debug-step-over"}"></ha-icon><span>${esc(this._t(occ.skipped ? "unskip" : "skip_next"))}</span></button>` : ""}
          ${armed
            ? this._chip("delete", "mdi:delete", this._t("confirm_delete"), "confirm", id)
            : this._chip("delete", "mdi:delete-outline", this._t("delete"), "rec", id)}
        </div>`
      : "";
    return `
      <div class="item ${on ? "" : "off"} ${open ? "open" : ""}">
        <button class="main-tap" data-act="toggle_open" data-id="${esc(id)}" aria-expanded="${open}">
          <span class="clock"><span class="tm">${esc(time)}</span><span class="wd">${esc(when)}</span></span>
          <span class="info">
            <span class="line"><ha-icon icon="${r.switch ? "mdi:television-play" : "mdi:bell-outline"}"></ha-icon>${esc(line)}</span>
            ${title ? `<span class="title">${esc(title)}</span>` : ""}
            <span class="meta">${meta.map((m) => `<span>${esc(m)}</span>`).join("")}</span>
          </span>
          <ha-icon class="chev" icon="${open ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
        </button>
        ${toggle}
        ${extra}
      </div>`;
  }

  _formHtml() {
    const f = this._form;
    const player = this._hass.states[findEntities(this._hass, this._config).player];
    const channels = channelsOf(player);
    const days = WEEKDAY_KEYS.map(
      (d) => `<button class="day ${f.days.includes(d) ? "sel" : ""}" data-act="day" data-day="${d}" aria-pressed="${f.days.includes(d)}">${esc(this._dayName(d))}</button>`
    ).join("");
    const valid = f.station_id && f.time && f.days.length;
    return `
      <div class="form">
        <div class="row2">
          <label class="field"><span>${esc(this._t("time"))}</span><input type="time" data-field="time" value="${esc(f.time)}"></label>
          <label class="pick nologo">
            <select data-field="station_id" aria-label="${esc(this._t("channel"))}">
              ${channels.map((c) => `<option value="${esc(c.id)}" ${c.id === f.station_id ? "selected" : ""}>${esc(c.name)}</option>`).join("")}
            </select>
            <ha-icon class="chev" icon="mdi:unfold-more-horizontal"></ha-icon>
          </label>
        </div>
        <div class="days">${days}</div>
        <label class="check"><input type="checkbox" data-field="switch" ${f.switch ? "checked" : ""}><span>${esc(this._t("switch_at_start"))}</span></label>
        <label class="check"><input type="checkbox" data-field="once" ${f.once ? "checked" : ""}><span>${esc(this._t("only_once"))}</span></label>
        <div class="actions">
          ${this._chip("form_cancel", "mdi:close", this._t("cancel"))}
          <button class="chip solid ${this._bz("form_save")}" data-act="form_save" ${valid ? "" : "disabled"}><ha-icon icon="mdi:check"></ha-icon><span>${esc(this._t("save"))}</span></button>
        </div>
      </div>`;
  }

  _css() {
    return `
      .head { padding: 14px 16px 6px; font-size: 16px; font-weight: 600; color: var(--primary-text-color); }
      .list { display: flex; flex-direction: column; padding: 4px 8px; }
      .item { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; border-radius: 12px; }
      .item + .item { border-top: 1px solid var(--divider-color); }
      .main-tap { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 12px; align-items: center;
        padding: 10px 6px 10px 8px; text-align: left; justify-content: stretch; border-radius: 12px; }
      .main-tap:hover { background: var(--secondary-background-color); }
      .clock { display: flex; flex-direction: column; align-items: flex-start; }
      .tm { font-size: 22px; font-weight: 700; line-height: 1.1; color: var(--accent-color); font-variant-numeric: tabular-nums; }
      .wd { font-size: 12px; color: var(--secondary-text-color); }
      .off .tm { color: var(--secondary-text-color); font-weight: 500; }
      .info { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
      .line { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: var(--primary-text-color);
        --mdc-icon-size: 18px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .line ha-icon { flex: none; color: var(--accent-color); }
      .off .line ha-icon { color: var(--secondary-text-color); }
      .off .line { color: var(--secondary-text-color); font-weight: 500; }
      .title { font-size: 13px; color: var(--primary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .meta { display: flex; flex-wrap: wrap; gap: 2px 10px; font-size: 12px; color: var(--secondary-text-color); }
      .chev { color: var(--secondary-text-color); --mdc-icon-size: 20px; }
      /* A switch like HA's own: the knob shows on/off. */
      .tgl { width: 44px; height: 26px; margin: 0 8px; border-radius: 13px; background: var(--divider-color); flex: none; }
      .tgl span { position: absolute; left: 3px; top: 3px; width: 20px; height: 20px; border-radius: 50%;
        background: var(--card-background-color); box-shadow: 0 1px 2px rgba(0, 0, 0, .3); transition: left .15s; }
      .tgl.on { background: var(--primary-color); }
      .tgl.on span { left: 21px; }
      .tgl.busy span { visibility: hidden; }
      .extra { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 8px; padding: 0 12px 12px 84px; }
      .chip.sel { background: color-mix(in srgb, var(--primary-color) 14%, transparent); }
      .chip.solid { background: var(--primary-color); color: var(--text-primary-color); border-color: var(--primary-color); }
      .chip[disabled] { opacity: .45; }
      .foot { padding: 8px 16px 16px; }
      .form { margin: 4px 12px 12px; padding: 12px; border-radius: 12px; background: var(--secondary-background-color);
        display: flex; flex-direction: column; gap: 12px; }
      .row2 { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 10px; align-items: end; }
      .field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--secondary-text-color); }
      .field input { all: unset; box-sizing: border-box; height: 44px; padding: 0 12px; border-radius: 22px; cursor: text;
        border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color);
        font-size: 15px; font-variant-numeric: tabular-nums; }
      .field input:focus { border-color: var(--primary-color); }
      .form .pick { background: var(--card-background-color); }
      .days { display: flex; flex-wrap: wrap; gap: 6px; }
      .day { height: 34px; min-width: 44px; padding: 0 10px; border-radius: 17px; font-size: 13px; font-weight: 500;
        color: var(--secondary-text-color); border: 1px solid var(--divider-color); background: var(--card-background-color); }
      .day.sel { background: var(--primary-color); color: var(--text-primary-color); border-color: var(--primary-color); }
      .check { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--primary-text-color); cursor: pointer; }
      .check input { width: 18px; height: 18px; accent-color: var(--primary-color); cursor: pointer; }
      .actions { display: flex; justify-content: flex-end; gap: 8px; }
      @container (max-width: 380px) { .extra { padding-left: 12px; } }
    `;
  }
}

// --- entities row: the channel picker -----------------------------------------
class WaipuChannelRow extends WaipuBase {
  setConfig(config) {
    this._config = { ...config };
    this._sig = null;
    this._render();
  }

  _signature() {
    const { player } = findEntities(this._hass, this._config);
    const s = this._hass.states[player];
    return [player, s?.attributes?.station_id, s?.attributes?.channels];
  }

  _draw() {
    const hass = this._hass;
    const { player } = findEntities(hass, this._config);
    const s = player ? hass.states[player] : null;
    const name = this._config.name || uiText("channel", hass);
    const icon = this._config.icon || "mdi:television-classic";
    const picker = s ? channelSelect(hass, player, s) : `<span class="none">${esc(uiText("no_player", hass))}</span>`;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: flex; align-items: center; gap: 16px; min-height: 40px; }
        .icon { width: 40px; display: flex; justify-content: center; color: var(--state-icon-color, var(--paper-item-icon-color)); }
        .name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .none, .msg { color: var(--secondary-text-color); font-size: 13px; }
        .msg { color: var(--error-color); }
        ${PICK_CSS}
        .pick { flex: 0 1 62%; height: 40px; }
        .pick select { line-height: 38px; }
      </style>
      <div class="icon"><ha-icon icon="${esc(icon)}"></ha-icon></div>
      <div class="name">${esc(name)}${this._message ? `<div class="msg">${esc(this._message)}</div>` : ""}</div>
      ${picker}`;
  }
}

// --- registration ---------------------------------------------------------------
// Loaded twice (e.g. an old hand-added resource next to the integration's
// copy)? Keep the first one instead of failing.
const ELEMENTS = [
  ["waipu-card", WaipuCard, "card_player"],
  ["waipu-channels-card", WaipuChannelsCard, "card_channels"],
  ["waipu-recordings-card", WaipuRecordingsCard, "card_recordings"],
  ["waipu-guide-card", WaipuGuideCard, "card_guide"],
  ["waipu-reminders-card", WaipuRemindersCard, "card_reminders"],
];
window.customCards = window.customCards || [];
for (const [tag, cls, key] of ELEMENTS) {
  if (customElements.get(tag)) continue;
  customElements.define(tag, cls);
  window.customCards.push({ type: tag, name: uiText(key), description: uiText(`${key}_text`), preview: false });
}
if (!customElements.get("waipu-channel-row")) customElements.define("waipu-channel-row", WaipuChannelRow);

console.info(`%c WAIPU-CARD %c ${CARD_VERSION} `, "font-weight:bold", "");
