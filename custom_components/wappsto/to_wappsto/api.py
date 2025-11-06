import logging
import wappstoiot
from pathlib import Path

from wappstoiot import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_STATE_CHANGED,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    EVENT_SERVICE_REGISTERED,
)
from homeassistant.core import Event, HomeAssistant

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id, DeviceInfo
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    entity_values as ev,
    entity as ent_help,
)

_LOGGER = logging.getLogger(__name__)

from ..const import (
    SUPPORTED_DOMAINS,
    INPUT_BOOLEAN,
    INPUT_BUTTON,
    BINARY_SENSOR,
    LIGHT,
    SENSOR,
    SWITCH,
    BUTTON,
    DEVICE_TRACKER, SESSION_KEY, ENTITY_LIST,
)
from ..binary_sensor import wappsto_connected_sensor
from .handle_input import HandleInput
from .handle_binary_sensor import HandleBinarySensor
from .handle_light import HandleLight
from .handle_sensor import HandleSensor
from .handle_switch import HandleSwitch
from .handle_button import HandleButton
from .handle_device_tracker import HandleDeviceTracker


class WappstoIoTApi:
    entity_list: list = []
    session: str = ""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        _LOGGER.info("TESTING WAPPSTO API __INIT__")
        self.hass = hass
        self.entity_list = entry.options[ENTITY_LIST]
        self.session = entry.data[SESSION_KEY]
        self.valueList = {}
        self.deviceList = {}
        self.handle_input = HandleInput(self.hass)
        self.handle_binary_sensor = HandleBinarySensor(self.hass)
        self.handle_sensor = HandleSensor(self.hass)
        self.handle_switch = HandleSwitch(self.hass)
        self.handle_button = HandleButton(self.hass)
        self.handle_light = HandleLight(self.hass)
        self.handle_device_tracker = HandleDeviceTracker(self.hass)

        self.handlerDomain = {}
        self.handlerDomain[INPUT_BUTTON] = self.handle_input
        self.handlerDomain[INPUT_BOOLEAN] = self.handle_input
        self.handlerDomain[BINARY_SENSOR] = self.handle_binary_sensor
        self.handlerDomain[LIGHT] = self.handle_light
        self.handlerDomain[SENSOR] = self.handle_sensor
        self.handlerDomain[SWITCH] = self.handle_switch
        self.handlerDomain[BUTTON] = self.handle_button
        self.handlerDomain[DEVICE_TRACKER] = self.handle_device_tracker

        wappstoiot.config(
            config_folder=Path(__file__).parent.parent,
            fast_send=False,
        )
        self.network = wappstoiot.createNetwork(name="HomeAssistant")
        self.temp_device = self.network.createDevice("Default device")

        def event_handler(event):
            self.handleEvent(event)

        def event_started(event):
            domain = event.data["domain"]
            _LOGGER.warning("Event started, domain: %s [%s]", domain, event)

        def event_ha_started(event):
            _LOGGER.info("HA started event")
            for values in self.entity_list:
                self.createValue(values)

        hass.bus.async_listen(event_type=EVENT_STATE_CHANGED, listener=event_handler)
        hass.bus.async_listen(  # NOTE: et it to work to create the value!!
            event_type=EVENT_SERVICE_REGISTERED, listener=event_started
        )

        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            event_ha_started,
        )

        hass.bus.async_listen(
            event_type=EVENT_HOMEASSISTANT_STOP,
            listener=lambda *args, **kwargs: wappstoiot.close(),
        )
        wappsto_connected_sensor.turn_on()

    def close(self):
        wappstoiot.close()

    def updateEntityList(self, entity_list: list):
        self.entity_list = entity_list
        for values in entity_list:
            self.createValue(values)

    def handleEvent(self, event):
        entity_id = event.data.get("entity_id", "")
        _LOGGER.info("Event id: %s [%s]", entity_id, event)
        (entity_type, entity_name) = entity_id.split(".")
        if entity_type in SUPPORTED_DOMAINS:
            self.updateValueReport(entity_id, event)

    def createOrGetDevice(self, entity_id: str) -> Device | None:
        entity_list = er.async_get(self.hass)
        tmp_entity = entity_list.async_get(entity_id)

        if not tmp_entity:
            return None
        dev_id = tmp_entity.device_id
        if not dev_id or len(dev_id) == 0:
            return None

        dev_list = dr.async_get(self.hass)
        tmp_dev = dev_list.async_get(str(dev_id))

        if tmp_dev is None:
            return None
        name = tmp_dev.name
        if name is None or len(name) == 0:
            return None

        if not dev_id in self.deviceList:
            illegal = wappstoiot.utils.name_check.illegal_characters(name)
            mapping_illegal = str.maketrans('', '', illegal)
            self.deviceList[dev_id] = self.network.createDevice(name.translate(mapping_illegal))

        return self.deviceList[dev_id]

    def createValue(self, entity_id: str):
        (entity_type, entity_name) = entity_id.split(".")
        if entity_type in SUPPORTED_DOMAINS:
            use_device = self.createOrGetDevice(entity_id)
            if not use_device:
                use_device = self.temp_device

            current_entity = self.hass.states.get(entity_id)
            initial_data = None
            if current_entity:
                _LOGGER.info(
                    "Set initial report[%s]:[%s]", entity_id, current_entity.state
                )
                initial_data = current_entity.state

            self.handlerDomain[entity_type].createValue(
                use_device, entity_type, entity_id, initial_data
            )

    def updateValueReport(self, entity_id, event):
        if not event.data["new_state"]:
            return
        testing = event.data["new_state"].state
        (entity_type, entity_name) = entity_id.split(".")
        self.handlerDomain[entity_type].getReport(
            entity_type, entity_id, testing, event
        )
