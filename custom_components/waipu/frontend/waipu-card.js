/*
 * waipu.tv cards for Home Assistant
 * Dashboard cards for the waipu.tv integration (KindOfNerdy/ha-waipu):
 *   waipu-card            the player (mode full, compact or row)
 *   waipu-channels-card   what's on now and next, per channel
 *   waipu-recordings-card the cloud recordings
 *   waipu-guide-card      the TV guide as a timeline
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
    card_player: "waipu.tv Player",
    card_player_text: "What's on the TV with picture and progress, controls, record button and a channel picker — full, compact or as a row.",
    card_channels: "waipu.tv Now on TV",
    card_channels_text: "Every channel with what's on now and next; tap to switch, record now, next or the series.",
    card_recordings: "waipu.tv Recordings",
    card_recordings_text: "Your cloud recordings with pictures — new, available and planned; play on the TV, stop or delete.",
    card_guide: "waipu.tv TV guide",
    card_guide_text: "The next hours as a timeline; watch, record or open details on the TV.",
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
    card_player: "waipu.tv Player",
    card_player_text: "Was am Fernseher läuft, mit Bild und Fortschritt, Steuerung, Aufnahme-Knopf und Senderauswahl — voll, kompakt oder als Zeile.",
    card_channels: "waipu.tv Jetzt im TV",
    card_channels_text: "Jeder Sender mit der laufenden und der nächsten Sendung; antippen schaltet um, aufnehmen jetzt, danach oder die Serie.",
    card_recordings: "waipu.tv Aufnahmen",
    card_recordings_text: "Deine Cloud-Aufnahmen mit Bild — neu, verfügbar und geplant; am TV abspielen, stoppen oder löschen.",
    card_guide: "waipu.tv Programm",
    card_guide_text: "Die nächsten Stunden als Zeitleiste; ansehen, aufnehmen oder Details am TV öffnen.",
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
  return { player, recordings, programs };
}

function channelsOf(stateObj) {
  const list = stateObj?.attributes?.channels;
  return Array.isArray(list) ? list : [];
}

function recordingsOf(hass, recordingsEntity) {
  const list = recordingsEntity ? hass.states[recordingsEntity]?.attributes?.recordings : null;
  return Array.isArray(list) ? list : [];
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
    if (!force && this.shadowRoot.activeElement?.tagName === "SELECT") {
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
    const r = ids.recordings ? this._hass.states[ids.recordings]?.last_updated : null;
    return [s?.attributes?.channels, s?.attributes?.station_id, s?.state, progs, r, this._open, this._config];
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
  }

  _draw() {
    const hass = this._hass;
    const ids = findEntities(hass, this._config);
    const player = hass.states[ids.player];
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
      const next = c.next ? `<div class="next"><span class="t">${esc(timeOf(hass, c.next.attributes.start_time))}</span>${esc(c.next.state)}</div>` : "";
      const recBtn = !canRecord
        ? ""
        : rec
          ? this._iconButton("stop_record", "mdi:stop-circle-outline", this._t("stop_record"), "rec", c.id).replace("data-act", `data-rec="${esc(rec)}" data-act`)
          : this._iconButton("record", "mdi:record-rec", this._t("record"), "rec", c.id);
      const extra = open
        ? `<div class="extra">
            ${now.description ? `<p>${esc(now.description)}</p>` : ""}
            <div class="chips">
              ${c.next && canRecord ? this._chip("record_next", "mdi:record", this._t("record_next"), "rec", c.id) : ""}
              ${now.series_id && canRecord ? this._chip("record_series", "mdi:record-rec", this._t("record_series"), "rec", c.id) : ""}
              ${player?.attributes?.target_android_tv ? this._chip("details", "mdi:information-outline", this._t("details_tv"), "", c.id) : ""}
            </div>
          </div>`
        : "";
      return `
        <div class="item ${tuned === c.id ? "tuned" : ""} ${open ? "open" : ""}">
          <button class="main-tap ${this._bz("tune" + c.id)}" data-act="tune" data-id="${esc(c.id)}"
            aria-label="${esc(this._t("watch"))}: ${esc(c.name)}">
            <div class="logo">${logo}</div>
            <div class="info">
              <div class="now">${rec ? `<span class="rec-mark"><ha-icon icon="mdi:record-circle"></ha-icon></span>` : ""}${esc(c.now.state)}</div>
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
      .logo { width: 64px; height: 36px; border-radius: 6px; display: flex; align-items: center; justify-content: center;
        background: var(--secondary-background-color); overflow: hidden; font-size: 11px; color: var(--secondary-text-color); }
      .logo img { width: 100%; height: 100%; object-fit: contain; padding: 4px; box-sizing: border-box; }
      .info { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
      .now { font-size: 15px; font-weight: 600; color: var(--primary-text-color); display: flex; align-items: center; gap: 4px;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .info .bar { height: 3px; }
      .meta { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--secondary-text-color); }
      .tuned .meta span:first-child { color: var(--accent-color); font-weight: 600; }
      .next { font-size: 12px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .next .t { font-variant-numeric: tabular-nums; margin-right: 6px; color: var(--primary-text-color); }
      .acts { display: flex; align-items: center; gap: 2px; padding-right: 4px; }
      .ctl { width: 40px; height: 40px; border-radius: 50%; color: var(--secondary-text-color); --mdc-icon-size: 22px; }
      .ctl:hover { background: var(--secondary-background-color); color: var(--primary-color); }
      .ctl.rec { color: var(--error-color); }
      .extra { grid-column: 1 / -1; padding: 0 12px 12px 88px; }
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
        color: var(--primary-color); --mdc-icon-size: 20px; opacity: 0; transition: opacity .15s; }
      button.main-tap:hover .playmark, button.main-tap:focus-visible .playmark { opacity: 1; }
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
    return [this._guide?.now, this._guide?.stations?.length, this._error, this._selected,
      p?.attributes?.station_id, p?.state, this._config];
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
    for (let m = 0; m <= minutes; m += 30) {
      const t = new Date(start.getTime() + m * 60000);
      marks.push(`<span class="mark ${m % 60 ? "half" : ""}" style="left:${m * GUIDE_PX_PER_MIN}px">${esc(timeOf(hass, t.toISOString()))}</span>`);
    }
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
          <span class="pt">${esc(p.title)}</span><span class="ps">${esc(timeOf(hass, p.start))}</span></button>`;
      });
      const logo = s.logo ? `<img src="${esc(s.logo)}" alt="${esc(s.name)}">` : `<span>${esc(s.name)}</span>`;
      return `<div class="grow ${tuned === s.id ? "tuned" : ""}"><div class="ch" title="${esc(s.name)}">${logo}</div>
        <div class="lane" style="width:${width}px">${blocks.join("")}</div></div>`;
    });

    this.shadowRoot.innerHTML = `
      <style>${BASE_CSS}${this._css()}</style>
      <ha-card>${head}
        <div class="scroller">
          <div class="grid" style="width:${width + 72}px">
            <div class="timeline"><div class="corner"></div><div class="scale" style="width:${width}px">${marks.join("")}</div></div>
            ${rows.join("")}
            <div class="nowline" style="left:${72 + nowX}px" aria-label="${esc(this._t("now_line"))}"></div>
          </div>
        </div>
        ${this._detail(g)}
        ${this._messageHtml()}
      </ha-card>`;
    // Open on "now", once; afterwards keep where the user scrolled.
    if (!this._scrolled) {
      const sc = this.shadowRoot.querySelector(".scroller");
      if (sc) {
        sc.scrollLeft = Math.max(0, nowX - 60);
        this._scrolled = true;
      }
    } else if (this._scrollLeft != null) {
      this.shadowRoot.querySelector(".scroller").scrollLeft = this._scrollLeft;
    }
    this.shadowRoot.querySelector(".scroller").addEventListener("scroll", (e) => {
      this._scrollLeft = e.target.scrollLeft;
    });
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
      .scroller { overflow-x: auto; overflow-y: hidden; overscroll-behavior-x: contain; scrollbar-width: thin; }
      .grid { position: relative; padding-bottom: 6px; }
      .timeline { display: flex; position: sticky; top: 0; height: 26px; }
      .corner { width: 72px; flex: none; position: sticky; left: 0; z-index: 3; background: var(--card-background-color); }
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
      .prog.now { background: color-mix(in srgb, var(--accent-color) 22%, var(--secondary-background-color)); }
      .prog.past { opacity: .5; }
      .prog.sel { box-shadow: inset 0 0 0 2px var(--primary-color); }
      .pt { font-size: 13px; font-weight: 600; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .ps { font-size: 11px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
      .recdot { position: absolute; top: 6px; right: 6px; width: 8px; height: 8px; border-radius: 50%;
        border: 2px solid var(--error-color); box-sizing: border-box; }
      .recdot.on { background: var(--error-color); }
      .nowline { position: absolute; top: 22px; bottom: 0; width: 2px; background: var(--error-color); z-index: 1;
        pointer-events: none; }
      .nowline::before { content: ""; position: absolute; top: -4px; left: -3px; width: 8px; height: 8px; border-radius: 50%;
        background: var(--error-color); }
      .detail { margin: 6px 12px 12px; padding: 12px; border-radius: 12px; background: var(--secondary-background-color); }
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
];
window.customCards = window.customCards || [];
for (const [tag, cls, key] of ELEMENTS) {
  if (customElements.get(tag)) continue;
  customElements.define(tag, cls);
  window.customCards.push({ type: tag, name: uiText(key), description: uiText(`${key}_text`), preview: false });
}
if (!customElements.get("waipu-channel-row")) customElements.define("waipu-channel-row", WaipuChannelRow);

console.info(`%c WAIPU-CARD %c ${CARD_VERSION} `, "font-weight:bold", "");
