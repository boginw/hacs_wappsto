"""The Wappsto integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .binary_sensor import wappsto_connected_sensor
from .const import (
    DOMAIN,
    ENTITY_LIST,
)
from .from_wappsto.api import WappstoApi
from .setup_network import (
    create_certificaties_files_if_not_exist,
    delete_certificate_files,
)
from .to_wappsto.api import WappstoIoTApi

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def update_listener(hass, entry):
    """Handle options update."""
    _LOGGER.error("UPDATE CONFIG NOT HANDLED: [%s]", entry.options)
    hass.data[DOMAIN][entry.entry_id].updateEntityList(entry.options[ENTITY_LIST])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    conf = entry.data

    _LOGGER.info("Async_setup_entry")
    # _LOGGER.warning("Configuration received: %s", conf)

    saved_files = await hass.async_add_executor_job(
        create_certificaties_files_if_not_exist, conf
    )
    if not saved_files:
        _LOGGER.error("Certificate files not found")

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    _LOGGER.info("STARTUP config: [%s]", entry.options)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    to_wappsto_api = await WappstoIoTApi.async_create(hass, entry)
    from_wappsto_api = WappstoApi(hass, entry)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "to_wappsto": to_wappsto_api,
        "from_wappsto": from_wappsto_api,
    }

    platforms = []
    if entry.options.get("import_devices"):
        platforms.append(Platform.SENSOR)
        platforms.append(Platform.SWITCH)

    if platforms:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

    from_wappsto_api.websocket_task = asyncio.create_task(
        from_wappsto_api.start_websocket(entry.options.get("import_devices"))
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.debug("Handling Wappsto options update")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    _LOGGER.info("Async_unload_entry - disconnect and clear certificates")
    entry_data = hass.data[DOMAIN][entry.entry_id]
    wappstoApi: WappstoIoTApi = entry_data["to_wappsto"]
    from_wappsto_api: WappstoApi = entry_data["from_wappsto"]
    wappstoApi.close()
    await from_wappsto_api.async_close()

    platforms = []
    if entry.options.get("import_devices"):
        platforms.extend([Platform.SENSOR, Platform.SWITCH])

    unload_ok = True
    if platforms:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    delete_certificate_files()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.info("Async_reload_entry")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
    # return True
