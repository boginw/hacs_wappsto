import logging

import wappstoiot
from homeassistant import exceptions
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity import get_device_class, get_unit_of_measurement
from wappstoiot import Device, Value, ValueTemplate

from .handler import Handler

_LOGGER = logging.getLogger(__name__)


class HandleSensor(Handler):
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.valueList: dict[str, Value] = {}

    def createValue(
        self, device: Device, domain: str, entity_id: str, initial_data: str | None
    ) -> None:
        valType = "unknown"
        createString = False
        try:
            device_class = get_device_class(self.hass, entity_id)
            if device_class:
                valType = device_class
                if (
                    SensorDeviceClass(device_class) == SensorDeviceClass.TIMESTAMP
                    or SensorDeviceClass(device_class) == SensorDeviceClass.DATE
                ):
                    createString = True
        except exceptions.HomeAssistantError as e:
            _LOGGER.error("Could not get device for entity: %s", entity_id)
            return None

        if createString:
            # noinspection PyTypeChecker
            self.valueList[entity_id] = device.createValue(
                name=entity_id,
                permission=wappstoiot.PermissionType.READ,
                value_template=ValueTemplate.STRING,
                period="0",
                delta="0"
            )
            if initial_data:
                self.valueList[entity_id].report(initial_data)
            return None

        measure = get_unit_of_measurement(self.hass, entity_id)

        # noinspection PyTypeChecker
        self.valueList[entity_id] = device.createNumberValue(
            name=entity_id,
            permission=wappstoiot.PermissionType.READ,
            type=valType,
            min=0 if measure == "%" else -60000,
            max=100 if measure == "%" else 60000,
            step=0.001,
            unit=measure if isinstance(measure, str) else "",
            period="0",
            delta="0",
        )
        if initial_data:
            try:
                self.valueList[entity_id].report(initial_data)
            except ValueError:
                _LOGGER.warning(
                    "Initial state for sensor '%s' is non-numeric ('%s'). Skipping initial report.",
                    entity_id,
                    initial_data,
                )

    def getReport(self, domain: str, entity_id: str, data: str, event: Event) -> None:
        if not entity_id in self.valueList:
            return
        try:
            self.valueList[entity_id].report(data)
        except ValueError:
            _LOGGER.warning(
                "Could not report new state for '%s': value is '%s'.", entity_id, data
            )

    def removeValue(self, entity_id: str) -> None:
        if entity_id in self.valueList:
            self.valueList[entity_id].delete()
            del self.valueList[entity_id]
