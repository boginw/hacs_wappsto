import logging
from homeassistant.core import Event, HomeAssistant
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import get_device_class
import wappstoiot
from wappstoiot import Device, Value
from .handler import Handler

_LOGGER = logging.getLogger(__name__)


class HandleBinarySensor(Handler):
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.valueList: dict[str, Value] = {}
        self.deviceClassMap = {
            BinarySensorDeviceClass.BATTERY: {
                "map": {"0": "normal", "1": "low"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.BATTERY_CHARGING: {
                "map": {"0": "not charging", "1": "charging"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.CO: {
                "map": {"0": "clear", "1": "detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.COLD: {
                "map": {"0": "normal", "1": "cold"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.CONNECTIVITY: {
                "map": {"0": "disconnected", "1": "connected"},
                "type": "connection",
            },
            BinarySensorDeviceClass.DOOR: {
                "map": {"0": "closed", "1": "open"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.GARAGE_DOOR: {
                "map": {"0": "closed", "1": "open"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.GAS: {
                "map": {"0": "clear", "1": "detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.HEAT: {
                "map": {"0": "normal", "1": "hot"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.LIGHT: {
                "map": {"0": "no light", "1": "light detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.LOCK: {
                "map": {"0": "locked", "1": "unlocked"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.MOISTURE: {
                "map": {"0": "dry", "1": "wet"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.MOTION: {
                "map": {"0": "clear", "1": "motion"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.MOVING: {
                "map": {"0": "stopped", "1": "moving"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.OCCUPANCY: {
                "map": {"0": "clear", "1": "detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.OPENING: {
                "map": {"0": "closed", "1": "open"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.PLUG: {
                "map": {"0": "unplugged", "1": "plugged in"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.POWER: {
                "map": {"0": "no power", "1": "power detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.PRESENCE: {
                "map": {"0": "away", "1": "home"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.PROBLEM: {
                "map": {"0": "OK", "1": "problem detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.RUNNING: {
                "map": {"0": "not running", "1": "running"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.SAFETY: {
                "map": {"0": "safe", "1": "unsafe"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.SMOKE: {
                "map": {"0": "clear", "1": "smoke detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.SOUND: {
                "map": {"0": "clear", "1": "sound detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.TAMPER: {
                "map": {"0": "clear", "1": "tampering detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.UPDATE: {
                "map": {"0": "up-to-date", "1": "update available"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.VIBRATION: {
                "map": {"0": "clear", "1": "vibration detected"},
                "type": "boolean",
            },
            BinarySensorDeviceClass.WINDOW: {
                "map": {"0": "closed", "1": "open"},
                "type": "boolean",
            },
        }

    # other helpers
    # def get_device_class(hass: HomeAssistant, entity_id: str)
    # def get_capability(hass: HomeAssistant, entity_id: str, capability: str)
    # def get_supported_features(hass: HomeAssistant, entity_id: str) -> int
    # def get_unit_of_measurement(hass: HomeAssistant, entity_id: str) -> str | None:

    def createValue(
        self, device: Device, domain: str, entity_id: str, initial_data: str | None
    ) -> None:
        device_class = get_device_class(self.hass, entity_id)

        mapping = {"0": "off", "1": "on"}
        valType = "boolean"

        if device_class:
            mapping = self.deviceClassMap[BinarySensorDeviceClass(device_class)]["map"]
            valType = self.deviceClassMap[BinarySensorDeviceClass(device_class)]["type"]

        self.valueList[entity_id] = device.createNumberValue(
            name=entity_id,
            permission=wappstoiot.PermissionType.READ,
            type=valType,
            min=0,
            max=1,
            step=1,
            unit="",
            mapping=mapping,
            meaningful_zero=True,
            ordered_mapping=True,
            period="0",
            delta="0.0",
        )
        if initial_data:
            self.valueList[entity_id].report("1" if initial_data == "on" else "0")

    def getReport(self, domain: str, entity_id: str, data: str, event: Event) -> None:
        if not entity_id in self.valueList:
            return
        self.valueList[entity_id].report("1" if data == "on" else "0")

    def removeValue(self, entity_id: str) -> None:
        if entity_id in self.valueList:
            self.valueList[entity_id].delete()
            del self.valueList[entity_id]
