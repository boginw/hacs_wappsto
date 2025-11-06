"""Support for Wappsto switches."""
from __future__ import annotations

import logging

from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from .wappsto_device import WappstoDevice, WappstoValue
from .. import WappstoApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wappsto switch from a config entry."""
    wappsto_api: WappstoApi = hass.data[DOMAIN][entry.entry_id]["from_wappsto"]

    if not entry.options.get("import_devices"):
        _LOGGER.info("No devices to import, skipping switch setup")
        return

    switches = []

    for device_id in entry.options["import_devices"]:
        device = await wappsto_api.get_device(device_id)

        for value in device.values.values():
            if value.permission == "rw" and value.type == "boolean":
                switches.append(WappstoSwitch(wappsto_api, device, value))

    _LOGGER.warning("Adding %s switches", len(switches))

    async_add_entities(switches)


class WappstoSwitch(SwitchEntity):
    """Representation of a Wappsto switch."""

    def __init__(
        self,
        wappsto_api: WappstoApi,
        device: WappstoDevice,
        value: WappstoValue,
    ) -> None:
        """Initialize the switch."""
        self._wappsto_api = wappsto_api
        self._device = device
        self._value = value
        self._attr_name = f"{device.name} {value.name}"
        self._attr_unique_id = f"{value.wappsto_id}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.wappsto_id)},
            name=self._device.name,
            manufacturer="Wappsto",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self._value.data == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._wappsto_api.send_command(self._value, "1")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._wappsto_api.send_command(self._value, "0")

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        def _update_callback():
            self.async_write_ha_state()

        self._wappsto_api.register_update_callback(
            self._value.wappsto_id, _update_callback
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        self._wappsto_api.unregister_update_callback(
            self._value.wappsto_id, lambda: self.async_write_ha_state()
        )
