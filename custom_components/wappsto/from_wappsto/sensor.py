"""Support for Wappsto sensors."""
from __future__ import annotations

import json
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .. import WappstoApi
from ..const import DOMAIN
from .wappsto_device import WappstoDevice, WappstoValue

_LOGGER = logging.getLogger(__name__)

WAPPSTO_VALUE_TYPE_TO_DEVICE_CLASS = {
    "power": SensorDeviceClass.POWER,
    "total_energy": SensorDeviceClass.ENERGY,
    "voltage": SensorDeviceClass.VOLTAGE,
    "electric_current": SensorDeviceClass.CURRENT,
    "frequency": SensorDeviceClass.FREQUENCY,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "humidity": SensorDeviceClass.HUMIDITY,
    "pressure": SensorDeviceClass.PRESSURE,
    "distance": SensorDeviceClass.DISTANCE,
    "speed": SensorDeviceClass.SPEED,
    "volume": SensorDeviceClass.VOLUME,
    "weight": SensorDeviceClass.WEIGHT,
    "co2": SensorDeviceClass.CO2,
    "co": SensorDeviceClass.CO,
    "voc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
}


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wappsto sensor from a config entry."""
    wappsto_api: WappstoApi = hass.data[DOMAIN][entry.entry_id]["from_wappsto"]

    if not entry.options["import_devices"]:
        _LOGGER.info("No devices to import, skipping sensor setup")
        return

    sensors = []

    for device_id in entry.options["import_devices"]:
        device = await wappsto_api.get_device(device_id)

        for value in device.values.values():
            if value.type in WAPPSTO_VALUE_TYPE_TO_DEVICE_CLASS:
                sensors.append(WappstoSensor(wappsto_api, device, value))

    _LOGGER.warning("Adding %s sensors", len(sensors))

    async_add_entities(sensors)


class WappstoSensor(SensorEntity):
    """Representation of a Wappsto sensor."""

    def __init__(
            self,
            wappsto_api,
            device: WappstoDevice,
            value: WappstoValue,
    ) -> None:
        """Initialize the sensor."""
        self._wappsto_api = wappsto_api
        self._device = device
        self._value = value
        self._attr_name = f"{device.name} {value.name}"
        self._attr_unique_id = f"{value.wappsto_id}"
        self._attr_device_class = WAPPSTO_VALUE_TYPE_TO_DEVICE_CLASS.get(value.type)
        self._attr_native_unit_of_measurement = value.unit

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.wappsto_id)},
            name=self._device.name,
            manufacturer="Wappsto",
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self._value.data == "":
            return None
        return self._value.data

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        def _update_callback():
            self.async_write_ha_state()

        self._wappsto_api.register_update_callback(self._value.wappsto_id, _update_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        self._wappsto_api.unregister_update_callback(self._value.wappsto_id, lambda: self.async_write_ha_state())
