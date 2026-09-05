"""DataUpdateCoordinator for the waipu.tv integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    Recording,
    Station,
    WaipuApiError,
    WaipuAuthError,
    WaipuClient,
    WaipuPermissionError,
)
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_SELECTED_CHANNELS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EPG_LOOKAHEAD,
    EPG_LOOKBEHIND,
    subscription_has_dvr,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class WaipuData:
    stations: list[Station]
    recordings: list[Recording]
    subscription: str
    user_handle: str

    @property
    def has_dvr(self) -> bool:
        return subscription_has_dvr(self.subscription)


class WaipuCoordinator(DataUpdateCoordinator[WaipuData]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WaipuClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.client = client
        # Shared "what's currently tuned" state — lives here rather than on
        # WaipuMediaPlayer so the channel select entity can read/write the
        # same value and both stay in sync via async_update_listeners().
        self.selected_station_id: str | None = None
        self.is_off: bool = False

    def _selected_station_ids(self, all_stations: list[Station]) -> list[str]:
        if (
            self.entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
            == ANDROID_TV_CHANNEL_VIEW_FAVORITES
        ):
            # Favorites-view mode: follow waipu's own favorite flag live,
            # ignoring any manually saved channel selection.
            return [s.id for s in all_stations if s.favorite and s.usable]
        selected = self.entry.options.get(CONF_SELECTED_CHANNELS)
        if selected:
            return [s.id for s in all_stations if s.id in set(selected)]
        # No selection yet → fetch EPG for favorites only to keep the load down
        favs = [s.id for s in all_stations if s.favorite and s.usable]
        if favs:
            return favs
        return [s.id for s in all_stations if s.usable][:25]

    async def _async_update_data(self) -> WaipuData:
        now = datetime.now(timezone.utc)
        try:
            stations = await self.client.get_stations()
            subscription = self.client.subscription
            user_handle = self.client.user_handle

            station_ids = self._selected_station_ids(stations)
            if station_ids:
                epg = await self.client.get_programs_in_window(
                    station_ids,
                    start=now - EPG_LOOKBEHIND,
                    end=now + EPG_LOOKAHEAD,
                )
            else:
                epg = {}

            enriched: list[Station] = []
            for s in stations:
                if s.id in epg:
                    enriched.append(replace(s, programs=tuple(epg[s.id])))
                else:
                    enriched.append(s)

            recordings: list[Recording] = []
            if subscription_has_dvr(subscription):
                try:
                    recordings = await self.client.get_recordings()
                except WaipuPermissionError:
                    _LOGGER.info(
                        "Subscription '%s' does not allow listing recordings",
                        subscription,
                    )

            _LOGGER.debug(
                "waipu refresh: subscription=%r, %d stations (%d usable), %d EPG slots, %d recordings",
                subscription,
                len(enriched),
                sum(1 for s in enriched if s.usable),
                sum(len(p) for p in epg.values()),
                len(recordings),
            )

            return WaipuData(
                stations=enriched,
                recordings=recordings,
                subscription=subscription,
                user_handle=user_handle,
            )
        except WaipuAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except WaipuApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

    # --- Convenience accessors used by entity platforms ---------------------
    def station(self, station_id: str) -> Station | None:
        if not self.data:
            return None
        return next((s for s in self.data.stations if s.id == station_id), None)

    @property
    def station_ids(self) -> list[str]:
        if not self.data:
            return []
        return [s.id for s in self.data.stations]
