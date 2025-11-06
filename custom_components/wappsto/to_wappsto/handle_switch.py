import logging

from homeassistant.core import Event, HomeAssistant
from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF

import wappstoiot
from wappstoiot import Device, Value
from .handler import Handler

_LOGGER = logging.getLogger(__name__)


class HandleSwitch(Handler):
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.valueList: dict[str, Value] = {}

    def createValue(
        self, device: Device, domain: str, entity_id: str, initial_data: str | None
    ) -> None:
        self.valueList[entity_id] = device.createNumberValue(
            name=entity_id,
            permission=wappstoiot.PermissionType.READWRITE,
            type="boolean",
            min=0,
            max=1,
            step=1,
            unit="",
            mapping={"0": "off", "1": "on"},
            meaningful_zero=True,
            ordered_mapping=True,
            period="0",
            delta="0.0",
        )

        def setControl(value, data):
            service_data = {
                "entity_id": entity_id,
            }
            self.hass.services.call(
                domain="switch",
                service=SERVICE_TURN_ON if data == 1 else SERVICE_TURN_OFF,
                service_data=service_data,
                blocking=False,
            )

        if initial_data:
            self.valueList[entity_id].report("1" if initial_data == "on" else "0")
            self.valueList[entity_id].control("1" if initial_data == "on" else "0")
        self.valueList[entity_id].onControl(callback=setControl)

    def getReport(self, domain: str, entity_id: str, data: str, event: Event) -> None:
        if not entity_id in self.valueList:
            return
        self.valueList[entity_id].report("1" if data == "on" else "0")

    def removeValue(self, entity_id: str) -> None:
        if entity_id in self.valueList:
            self.valueList[entity_id].delete()
            del self.valueList[entity_id]
