"""DataUpdateCoordinator for the OpenMotics integration."""
from __future__ import annotations

import asyncio
import logging

from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyhaopenmotics.errors import (  # OpenMoticsConnectionError,; OpenMoticsConnectionTimeoutError,; OpenMoticsRateLimitError,; # OpenMoticsAuthenticationError,
    ApiException,
)
from pyhaopenmotics.openmotics import CloudClient, LocalGatewayClient

from .const import CONF_INSTALLATION_ID, DEFAULT_HOST, DEFAULT_SCAN_INTERVAL, DOMAIN
from .exceptions import CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)


class OpenMoticsDataUpdateCoordinator(DataUpdateCoordinator):
    """Query OpenMotics devices and keep track of seen conditions."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the OpenMotics gateway."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.hass = hass
        # self.entry = entry
        self._install_id = entry.data.get(CONF_INSTALLATION_ID)

        """Set up a OpenMotics controller"""
        if entry.data.get(CONF_HOST) == DEFAULT_HOST:
            self._omclient = CloudClient(
                client_id=entry.data.get(CONF_CLIENT_ID),
                client_secret=entry.data.get(CONF_CLIENT_SECRET),
            )
        else:
            self._omclient = LocalGatewayClient(
                client_id=entry.data.get(CONF_CLIENT_ID),
                client_secret=entry.data.get(CONF_CLIENT_SECRET),
                server=entry.data.get(CONF_HOST),
                port=entry.data.get(CONF_PORT),
                ssl=entry.data.get(CONF_VERIFY_SSL),
            )

    async def get_token(self) -> bool:
        """Login to OpenMotics cloud / gateway."""
        _LOGGER.debug("Logging in via get_token to installation: %s", self._install_id)
        try:
            await self._omclient.get_token()

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout connecting to the OpenMoticsApi")
            raise CannotConnect

        except ApiException as err:
            _LOGGER.error("Error connecting to the OpenMoticsApi")
            # _LOGGER.error(err)
            raise ConfigEntryNotReady(
                f"Unable to connect to OpenMoticsApi: {err}"
            ) from err

        return True

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables so entities can quickly look up their data.
        """

        try:
            my_outputs = await self._omclient.outputs.get_all(self.install_id)
            my_lights = await self._omclient.lights.get_all(self.install_id)
            my_groupactions = await self._omclient.groupactions.get_all(self.install_id)
            my_shutters = await self._omclient.shutters.get_all(self.install_id)
            my_sensors = await self._omclient.sensors.get_all(self.install_id)

        except ApiException as err:
            _LOGGER.error("Could not retrieve the data from the OpenMotics API")
            _LOGGER.error("Too many errors: %s", err)
            return {
                "lights": [],
                "outputs": [],
                "groupactions": [],
                "shutters": [],
                "sensors": [],
            }
        # Store data in a way Home Assistant can easily consume it
        return {
            "outputs": my_outputs,
            "lights": my_lights,
            "groupactions": my_groupactions,
            "shutters": my_shutters,
            "sensors": my_sensors,
        }

    @property
    def install_id(self) -> str:
        """Return the name of the device."""
        return self._install_id

    @property
    def omclient(self) -> Any:
        """Return the backendclient."""
        return self._omclient
