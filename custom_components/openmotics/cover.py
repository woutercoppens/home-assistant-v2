"""Support for HomeAssistant shutters."""
from __future__ import annotations

import logging

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .entity import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up covers for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for index, om_cover in enumerate(coordinator.data["shutters"]):
        if (
            om_cover.name is None
            or om_cover.name == ""
            or om_cover.name == NOT_IN_USE
        ):
            continue
        # print("- {}".format(om_cover))
        entities.append(OpenMoticsShutter(coordinator, index, om_cover))

    if not entities:
        _LOGGER.info("No OpenMotics shutters added")
        return False

    async_add_entities(entities)


class OpenMoticsShutter(OpenMoticsDevice, CoverEntity):
    """Representation of a OpenMotics shutter."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, index, device):
        """Initialize the shutter."""
        super().__init__(coordinator, index, device, "cover")
        
        self._device = self.coordinator.data["shutters"][self.index]
  
    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is None:
            return None
        return self.current_cover_position == 0

    @property
    def current_cover_position(self):
        """Return the current position of cover."""
        # None is unknown, 0 is closed, 100 is fully open.
        return self._device.status.position

    async def async_open_cover(self, **kwargs):
        """Open the window cover."""
        await self.coordinator.omclient.shutters.up(
            self.install_id,
            self.device_id,
        )
        await self.coordinator.async_refresh()

    async def async_close_cover(self, **kwargs):
        """Open the window cover."""
        await self.coordinator.omclient.shutters.down(
            self.install_id,
            self.device_id,
        )
        await self.coordinator.async_refresh()

    async def async_stop_cover(self, **kwargs):
        """Stop the window cover."""
        await self.coordinator.omclient.shutters.stop(
            self.install_id,
            self.device_id,
        )
        await self.coordinator.async_refresh()
