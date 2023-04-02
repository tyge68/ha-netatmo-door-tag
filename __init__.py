"""The Netatmo Door Tags integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA,
)
from homeassistant.helpers import config_validation as cv
from .const import CONF_HOME_ID, CONF_AUTH_FILE, NETATMO_DOMAIN
import asyncio
import voluptuous as vol
import logging

DEFAULT_NAME = "Netatmo Door Tag"
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOME_ID): cv.string,
        vol.Required(CONF_AUTH_FILE): cv.string,
    }
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Netatmo Door Tags integration component."""

    async def _handle_reload(service):
        """Handle reload service call."""
        _LOGGER.info("Service %s.reload called: reloading integration", NETATMO_DOMAIN)
        current_entries = hass.config_entries.async_entries(NETATMO_DOMAIN)

        reload_tasks = [
            hass.config_entries.async_setup_platforms(entry, (Platform.BINARY_SENSOR))
            for entry in current_entries
        ]

        await asyncio.gather(*reload_tasks)

    hass.helpers.service.async_register_admin_service(
        NETATMO_DOMAIN,
        SERVICE_RELOAD,
        _handle_reload,
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Netatmo Door Tags from a config entry."""
    # TODO Optionally store an object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = ...

    # TODO Optionally validate config entry options before setting up platform

    hass.config_entries.async_setup_platforms(entry, (Platform.BINARY_SENSOR))
    # hass.helpers.discovery.load_platform("climate", DOMAIN, {}, entry)

    # TODO Remove if the integration does not have an options flow
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


# TODO Remove if the integration does not have an options flow
async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, (Platform.BINARY_SENSOR)
    ):
        hass.data[NETATMO_DOMAIN].pop(entry.entry_id)

    return unload_ok
