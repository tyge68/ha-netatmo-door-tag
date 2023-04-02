"""Platform to present any Tuya DP as a binary sensor."""
import asyncio
import logging
import time

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .netatmo import Authenticator, HomeStatus, HomesData
from .const import CONF_HOME_ID, CONF_AUTH_FILE

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType,
) -> None:
    """Set up the climate platform."""
    home_id = config[CONF_HOME_ID]
    auth_file = config[CONF_AUTH_FILE]
    home_status_cache = HomeStatusCache(hass, home_id, auth_file)
    last_cached_status = await home_status_cache.get_cached_status()
    entities = []
    for doortag in last_cached_status:
        entities.append(
            NetatmoDoorTagBinarySensor(
                home_status_cache, doortag["name"], doortag["status"]
            )
        )
    add_entities(entities, False)


class HomeStatusCache:
    """Representation of a Netatmo Door Tag Home Status cache."""

    def __init__(self, hass, home_id, auth_file) -> None:
        self._hass = hass
        self._home_id = home_id
        self._auth_file = auth_file
        self._next_update = -1
        self._cached_status = None
        self._lock = asyncio.Lock()

    async def update_cache(self) -> None:
        """Function to update cache if outdated"""
        async with self._lock:
            curr_time = time.time()
            _LOGGER.info(
                "Current time %s vs next update = %s",
                str(curr_time),
                str(self._next_update),
            )
            if curr_time > self._next_update:
                _LOGGER.info("Update Required")
                authenticator = Authenticator(self._hass, self._auth_file)
                await authenticator.init()
                _LOGGER.info("Calling HomesData")
                homedata = HomesData(authenticator, self._home_id)
                await homedata.init()
                _LOGGER.info("Calling HomeStatus")
                homestatus = HomeStatus(authenticator, self._home_id, homedata)
                await homestatus.init()
                self._cached_status = homestatus.door_tags
                self._next_update = time.time() + 59
            else:
                _LOGGER.info("No updated needed")

    async def get_cached_status(self) -> list:
        """Function to get status from cache if possible"""
        await self.update_cache()
        return self._cached_status


class NetatmoDoorTagBinarySensor(BinarySensorEntity):
    """Representation of a Netatmo Door Tag binary sensor."""

    def __init__(
        self, home_status_cache: HomeStatusCache, name: str, initial_status: bool
    ) -> None:
        self._home_status_cache = home_status_cache
        self._attr_name = name
        self._is_on = initial_status != "closed"

    @property
    def is_on(self) -> bool:
        """Return sensor state."""
        return self._is_on

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._attr_name

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._attr_name

    @property
    def device_class(self):
        """Return the class of this device."""
        return BinarySensorDeviceClass.DOOR

    async def async_update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        last_cached_status = await self._home_status_cache.get_cached_status()
        for doortag in last_cached_status:
            if doortag["name"] == self._attr_name:
                status = doortag["status"]
                self._is_on = status != "closed"
