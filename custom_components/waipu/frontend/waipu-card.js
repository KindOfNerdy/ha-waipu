/*
 * waipu.tv cards for Home Assistant
 * Dashboard cards for the waipu.tv integration (KindOfNerdy/ha-waipu).
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
    failed: "That didn't work: {error}",
    ed_entity: "waipu player (only needed with more than one)",
    ed_hide: "Hide",
    ed_hide_picture: "Picture",
    ed_hide_progress: "Progress bar",
    ed_hide_controls: "Controls",
    ed_hide_record: "Record button",
    ed_hide_channels: "Channel picker",
    ed_hide_off_hint: "\"TV is off\" line with its power button",
    ed_layout: "Layout",
    ed_layout_full: "Full: big picture and controls",
    ed_layout_compact: "Compact: small picture and channel picker, e.g. under a remote",
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
    failed: "Das hat nicht geklappt: {error}",
    ed_entity: "waipu-Player (nur nötig, wenn es mehrere gibt)",
    ed_hide: "Ausblenden",
    ed_hide_picture: "Bild",
    ed_hide_progress: "Fortschrittsbalken",
    ed_hide_controls: "Steuerung",
    ed_hide_record: "Aufnahme-Knopf",
    ed_hide_channels: "Senderauswahl",
    ed_hide_off_hint: "Zeile „Fernseher ist aus“ samt Ein-Knopf",
    ed_layout: "Darstellung",
    ed_layout_full: "Voll: großes Bild und Steuerung",
    ed_layout_compact: "Kompakt: kleines Bild und Senderauswahl, z. B. unter einer Fernbedienung",
  },
};

// Media player feature bits (homeassistant.components.media_player)
const F = { PAUSE: 1, SEEK: 2, PREVIOUS: 16, NEXT: 32, TURN_ON: 128, TURN_OFF: 256, PLAY: 16384 };
const HIDE_KEYS = ["picture", "progress", "controls", "record", "channels", "off_hint"];
const LAYOUTS = ["full", "compact"];
const SEEK_STEP = 30;

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

function has(stateObj, bit) {
  return ((stateObj?.attributes?.supported_features || 0) & bit) === bit;
}

// The integration's entities, found by platform and translation key — no
// entity ids to configure. Returns the waipu media_player (or the one the
// config names) and the recordings sensor if there is one (DVR plan).
function findEntities(hass, config) {
  const entries = Object.values(hass?.entities || {}).filter((e) => e.platform === DOMAIN);
  const players = entries.filter((e) => e.entity_id.startsWith("media_player."));
  const player = config?.entity || players[0]?.entity_id || null;
  const recordings = entries.find((e) => e.translation_key === "all_recordings")?.entity_id || null;
  return { player, recordings };
}

function channelsOf(stateObj) {
  const list = stateObj?.attributes?.channels;
  return Array.isArray(list) ? list : [];
}

function callService(el, hass, domain, service, data) {
  return hass.callService(domain, service, data).catch((err) => {
    el._message = uiText("failed", hass).replace("{error}", err?.message || err);
    el._render(true);
    clearTimeout(el._messageTimer);
    el._messageTimer = setTimeout(() => {
      el._message = "";
      el._render(true);
    }, 6000);
  });
}

function channelSelect(hass, player, stateObj, cls = "") {
  const channels = channelsOf(stateObj);
  if (!channels.length) return "";
  const current = stateObj.attributes.station_id;
  const active = channels.find((c) => c.id === current);
  // Only a real channel logo goes in front; without one the text starts left.
  const logo = active?.logo ? `<img class="logo" src="${esc(active.logo)}" alt="">` : "";
  return `
    <label class="pick ${logo ? "" : "nologo"} ${cls}">
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

// The picker: a field with the channel's logo in front and a chevron behind,
// so it reads as something to open.
const PICK_CSS = `
  .pick { position: relative; display: flex; align-items: center; min-width: 0; height: 44px;
    border: 1px solid var(--divider-color); border-radius: 22px; background: var(--secondary-background-color);
    transition: border-color .15s; }
  .pick:hover { border-color: var(--primary-color); }
  .pick:focus-within { border-color: var(--primary-color); box-shadow: 0 0 0 1px var(--primary-color); }
  .pick .logo { position: absolute; left: 6px; width: 48px; height: 32px; object-fit: contain; pointer-events: none;
    --mdc-icon-size: 20px; display: flex; align-items: center; justify-content: center; color: var(--secondary-text-color); }
  .pick select { all: unset; box-sizing: border-box; width: 100%; height: 100%; padding: 0 40px 0 62px; cursor: pointer;
    line-height: 42px; color: var(--primary-text-color); font-size: 15px; font-weight: 500;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pick select option { background: var(--card-background-color); color: var(--primary-text-color); }
  .pick.nologo select { padding-left: 16px; }
  .pick .chev { position: absolute; right: 12px; pointer-events: none; color: var(--primary-color); --mdc-icon-size: 20px; }
`;

// Shared behaviour of the card and the entities row: picking a channel in
// the drop-down switches to it; while the drop-down is open, updates wait.
class WaipuBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._message = "";
    this._sig = null;
    this.shadowRoot.addEventListener("change", (e) => {
      const sel = e.target.closest("select[data-act='channel']");
      if (!sel || !sel.value) return;
      callService(this, this._hass, "media_player", "play_media", {
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
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  // Redraw only when something shown changed; never while a drop-down is open.
  _render(force = false) {
    if (!this._hass || !this._config) return;
    const sig = this._signature();
    if (!force && sig === this._sig) return;
    if (!force && this.shadowRoot.activeElement?.tagName === "SELECT") {
      this._held = true;
      return;
    }
    this._sig = sig;
    this._draw();
  }
}

class WaipuCard extends WaipuBase {
  constructor() {
    super();
    this.shadowRoot.addEventListener("click", (e) => {
      const el = e.target.closest("[data-act]");
      if (!el || el.disabled || el.tagName === "SELECT") return;
      this._act(el.dataset.act);
    });
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", selector: { entity: { filter: { domain: "media_player", integration: DOMAIN } } } },
        {
          name: "layout",
          default: "full",
          selector: { select: { mode: "list", options: LAYOUTS.map((k) => ({ value: k, label: uiText(`ed_layout_${k}`) })) } },
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
      ],
      computeLabel: (schema) => uiText(`ed_${schema.name}`),
    };
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (config.hide && !Array.isArray(config.hide)) throw new Error("hide must be a list");
    if (config.layout && !LAYOUTS.includes(config.layout)) throw new Error("layout must be full or compact");
    const compact = config.layout === "compact";
    // Compact sits under a remote: no transport controls unless asked for.
    const hide = config.hide || (compact ? ["controls"] : []);
    this._config = { ...config, layout: compact ? "compact" : "full", hide };
    this._sig = null;
    this._render();
  }

  getCardSize() {
    return this._config?.layout === "compact" ? 2 : 5;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  connectedCallback() {
    // Live progress moves with the clock, on-demand progress with the position.
    this._tick = setInterval(() => this._updateProgress(), 1000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
  }

  _t(key) {
    return uiText(key, this._hass);
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
    return JSON.stringify([
      player,
      s?.state,
      s?.attributes,
      r?.last_updated,
      this._message,
      lang(this._hass),
      this._config,
    ]);
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
    const { recordings } = this._ids();
    const list = recordings ? this._hass.states[recordings]?.attributes?.recordings : null;
    if (!Array.isArray(list) || !s.attributes.station_id) return false;
    return list.some((r) => r.status === "RECORDING" && r.station_id === s.attributes.station_id);
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
      const start = new Date(a.start_time).getTime();
      const stop = new Date(a.stop_time).getTime();
      const now = Date.now() - (a.timeshift_minutes || 0) * 60000;
      if (stop <= start) return null;
      const pct = Math.min(Math.max(((now - start) / (stop - start)) * 100, 0), 100);
      return { pct, left: Math.max(Math.round((stop - now) / 60000), 0) };
    }
    return null;
  }

  _updateProgress() {
    if (!this._hass || this._hidden("progress")) return;
    const s = this._hass.states[this._ids().player];
    const bar = this.shadowRoot.querySelector(".bar div");
    const left = this.shadowRoot.querySelector(".left");
    if (!s || !bar) return;
    const p = this._progress(s);
    if (!p) return;
    bar.style.width = `${p.pct.toFixed(2)}%`;
    if (left) left.textContent = this._t("left").replace("{min}", p.left);
    const from = this.shadowRoot.querySelector(".from");
    if (from && p.pos != null) from.textContent = clock(p.pos);
  }

  _time(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleTimeString(lang(this._hass), { hour: "2-digit", minute: "2-digit" });
  }

  _act(act) {
    const hass = this._hass;
    const entity_id = this._ids().player;
    const s = hass.states[entity_id];
    if (!s) return;
    const mp = (service, data = {}) => callService(this, hass, "media_player", service, { entity_id, ...data });
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
    if (act === "restart") callService(this, hass, DOMAIN, "restart_program", {});
    if (act === "record") callService(this, hass, DOMAIN, "create_recording", {});
    if (act === "stop_record") callService(this, hass, DOMAIN, "stop_recording", {});
  }

  _button(act, icon, label, { primary = false, disabled = false } = {}) {
    return `<button class="ctl ${primary ? "primary" : ""}" data-act="${act}" title="${esc(label)}"
      aria-label="${esc(label)}" ${disabled ? "disabled" : ""}><ha-icon icon="${icon}"></ha-icon></button>`;
  }

  _draw() {
    const hass = this._hass;
    const { player, recordings } = this._ids();
    const s = player ? hass.states[player] : null;
    if (!s) {
      this.shadowRoot.innerHTML = `<style>${this._css()}</style><ha-card><div class="empty">${esc(this._t("no_player"))}</div></ha-card>`;
      return;
    }
    const a = s.attributes;
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
    if (recording) status.push(`<span class="rec"><ha-icon icon="mdi:record-circle"></ha-icon>${esc(this._t("recording_now"))}</span>`);

    const canPower = has(s, off ? F.TURN_ON : F.TURN_OFF);
    const power = canPower
      ? `<button class="power ${off ? "" : "on"}" data-act="power" title="${esc(this._t(off ? "power_on" : "power_off"))}"
          aria-label="${esc(this._t(off ? "power_on" : "power_off"))}"><ha-icon icon="mdi:power"></ha-icon></button>`
      : "";

    // The program's slot: air time live, position on demand.
    let slot = "";
    if (progress) {
      const live = kind === "live";
      const from = live ? this._time(a.start_time) : progress.pos != null ? clock(progress.pos) : "";
      const to = live ? this._time(a.stop_time) : a.media_duration ? clock(a.media_duration) : "";
      slot = `<div class="slot">
          <div class="bar"><div style="width:${progress.pct.toFixed(2)}%"></div></div>
          <div class="ends"><span class="from">${esc(from)}</span><span class="left">${esc(leftText)}</span><span>${esc(to)}</span></div>
        </div>`;
    }

    let controls = "";
    if (!off && !this._hidden("controls")) {
      const side = [];
      const main = [];
      if (has(s, F.PREVIOUS)) main.push(this._button("previous", "mdi:skip-previous", this._t("previous")));
      const seekable = has(s, F.SEEK) && (onDemand || kind === "live");
      if (seekable) main.push(this._button("back", "mdi:rewind-30", this._t("back")));
      if (s.state === "paused" && has(s, F.PLAY)) main.push(this._button("play", "mdi:play", this._t("play"), { primary: true }));
      else if (s.state === "playing" && has(s, F.PAUSE)) main.push(this._button("pause", "mdi:pause", this._t("pause"), { primary: true }));
      // Live, forward only goes as far as live itself.
      if (seekable && (onDemand || (a.timeshift_seconds || 0) >= SEEK_STEP)) {
        main.push(this._button("forward", "mdi:fast-forward-30", this._t("forward")));
      }
      if (has(s, F.NEXT)) main.push(this._button("next", "mdi:skip-next", this._t("next")));
      if (kind === "live" && a.restart_available) side.push(this._labelButton("restart", "mdi:restart", this._t("restart")));
      if (kind === "live" && recordings && !this._hidden("record")) {
        if (recording) side.push(this._labelButton("stop_record", "mdi:stop", this._t("stop_record"), "rec"));
        else if (a.recordable) side.push(this._labelButton("record", "mdi:record", this._t("record"), "rec"));
      }
      if (main.length || side.length) {
        controls = `<div class="controls">${main.length ? `<div class="main">${main.join("")}</div>` : ""}
          ${side.length ? `<div class="side">${side.join("")}</div>` : ""}</div>`;
      }
    }

    const picker = this._hidden("channels") ? "" : channelSelect(hass, player, s);
    const message = this._message ? `<div class="msg" role="alert">${esc(this._message)}</div>` : "";

    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>
      <ha-card class="${off ? "off" : ""} ${showPic ? "has-pic" : "no-pic"} ${this._config.layout}">
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
          ${message}
        </div>
      </ha-card>`;
  }

  _labelButton(act, icon, label, cls = "") {
    return `<button class="chip ${cls}" data-act="${act}"><ha-icon icon="${icon}"></ha-icon><span>${esc(label)}</span></button>`;
  }

  _css() {
    return `
      :host { display: block; container-type: inline-size; }
      ha-card { overflow: hidden; }
      .empty { padding: 16px; color: var(--secondary-text-color); }

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
      .live { display: inline-flex; align-items: center; gap: 6px; color: var(--error-color); font-weight: 600; }
      .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--error-color); animation: onair 2s ease-in-out infinite; }
      @keyframes onair { 50% { opacity: .35; } }
      @media (prefers-reduced-motion: reduce) { .dot { animation: none; } }
      .kind { font-weight: 600; color: var(--primary-text-color); }
      .rec { display: inline-flex; align-items: center; gap: 4px; color: var(--error-color); }
      .rec ha-icon { --mdc-icon-size: 16px; }
      .title { font-size: 22px; font-weight: 700; line-height: 1.2; letter-spacing: -0.01em; color: var(--primary-text-color);
        overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-wrap: balance; }
      .off .title { font-size: 18px; font-weight: 500; color: var(--secondary-text-color); }
      .channel { font-size: 15px; font-weight: 500; color: var(--primary-text-color); }
      .episode { font-size: 14px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

      button { all: unset; box-sizing: border-box; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
        -webkit-tap-highlight-color: transparent; }
      button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .power { position: absolute; top: 12px; right: 12px; z-index: 2; width: 40px; height: 40px; border-radius: 50%;
        color: var(--secondary-text-color); border: 1px solid var(--divider-color);
        background: color-mix(in srgb, var(--card-background-color) 75%, transparent); backdrop-filter: blur(6px); }
      .power.on { color: var(--primary-color); border-color: color-mix(in srgb, var(--primary-color) 60%, transparent); }
      .power:hover { background: var(--secondary-background-color); }
      .off .power { width: 48px; height: 48px; top: 8px; color: var(--primary-color); border-color: var(--primary-color); --mdc-icon-size: 26px; }

      .body { padding: 8px 16px 16px; display: flex; flex-direction: column; gap: 14px; }
      .body:first-child { padding-top: 16px; }
      .slot { display: flex; flex-direction: column; gap: 6px; }
      .bar { height: 4px; border-radius: 2px; background: var(--divider-color); overflow: hidden; }
      .bar div { height: 100%; background: var(--accent-color); transition: width 1s linear; }
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
      .chip { gap: 6px; height: 36px; padding: 0 14px 0 10px; border-radius: 18px; font-size: 14px; font-weight: 500;
        color: var(--primary-color); border: 1px solid color-mix(in srgb, var(--primary-color) 55%, transparent); --mdc-icon-size: 18px; }
      .chip:hover { background: color-mix(in srgb, var(--primary-color) 12%, transparent); }
      .chip.rec { color: var(--error-color); border-color: color-mix(in srgb, var(--error-color) 55%, transparent); }
      .chip.rec:hover { background: color-mix(in srgb, var(--error-color) 12%, transparent); }
      .msg { font-size: 13px; color: var(--error-color); }
      ${PICK_CSS}

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

// A row for the entities card: "Channel" with the drop-down next to it.
class WaipuChannelRow extends WaipuBase {
  setConfig(config) {
    this._config = { ...config };
    this._sig = null;
    this._render();
  }

  _signature() {
    const { player } = findEntities(this._hass, this._config);
    const s = this._hass.states[player];
    return JSON.stringify([player, s?.attributes?.station_id, s?.attributes?.channels, this._message, lang(this._hass)]);
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

// Loaded twice (e.g. an old hand-added resource next to the integration's
// copy)? Keep the first one instead of failing.
if (!customElements.get("waipu-card")) {
  customElements.define("waipu-card", WaipuCard);
  customElements.define("waipu-channel-row", WaipuChannelRow);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "waipu-card",
    name: "waipu.tv Player",
    description: "What's on the TV with picture and progress, playback controls, record button and a channel picker.",
    preview: false,
  });
}

console.info(`%c WAIPU-CARD %c ${CARD_VERSION} `, "font-weight:bold", "");
