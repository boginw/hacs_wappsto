from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add sensors for passed config_entry in HA."""
    hub = hass.data[DOMAIN][config_entry.entry_id]

    _LOGGER.info("Testing hass.data[DOMAIN] [%s]", hass.data[DOMAIN])
    _LOGGER.info("Asyc setup_entry")

    new_devices = []
    new_devices.append(wappsto_connected_sensor)
    async_add_entities(new_devices, True)


class __OnlineOfflineEntity(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    # device_class = BinarySensorDeviceClass.CONNECTIVITY

    _LOGGER.info("OnlineOfflineEntity")

    def __init__(self) -> None:
        self._is_on = "off"
        # self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id = "wapp_online_offline_id"
        self._attr_name = "Wappsto connection"

    # def device_info(self) -> DeviceInfo:
    #     """Return the device info."""
    #     return DeviceInfo(
    #         identifiers={
    #             # Serial numbers are unique identifiers within a specific domain
    #             (DOMAIN, self.unique_id)
    #         },
    #         name="wappsto test",
    #         manufacturer="Seluxit",
    #         model="test model",
    #         sw_version="Current sw test version",
    #         # via_device=(hue.DOMAIN, self.api.bridgeid),
    #     )

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    @property
    def state(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = "on"

    async def async_turn_off(self, **kwargs):
        self._is_on = "off"

    def turn_on(self, **kwargs):
        self._is_on = "on"

    def turn_off(self, **kwargs):
        self._is_on = "off"


wappsto_connected_sensor = __OnlineOfflineEntity()
