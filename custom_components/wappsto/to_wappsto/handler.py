from abc import ABC, abstractmethod
from homeassistant.core import HomeAssistant, Event

from wappstoiot import Device, Value

# from homeassistant.helpers.entity import get_device_class, get_capability, get_supported_features, get_unit_of_measurement
#
# def get_device_class(hass: HomeAssistant, entity_id: str)
# def get_capability(hass: HomeAssistant, entity_id: str, capability: str)
# def get_supported_features(hass: HomeAssistant, entity_id: str) -> int
# def get_unit_of_measurement(hass: HomeAssistant, entity_id: str) -> str | None:


class Handler(ABC):
    @abstractmethod
    def __init__(self, hass: HomeAssistant) -> None:
        pass

    @abstractmethod
    def createValue(
        self, device: Device, domain: str, entity_id: str, initial_data: str | None
    ) -> None:
        pass

    @abstractmethod
    def getReport(self, domain: str, entity_id: str, data: str, event: Event) -> str:
        pass
