from typing import Any
import logging
import struct

from homeassistant.core import Event, State, HomeAssistant
from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF

from homeassistant.components.light import (
    ColorMode,
    ATTR_COLOR_MODE,
    ATTR_SUPPORTED_COLOR_MODES,
)


import wappstoiot
from wappstoiot import Device, Value
from .handler import Handler

ONOFF_VALUE = "onoff"
BRIGHTNESS_VALUE = "brightness"
COLOR_VALUE = "color"
COLOR_TEMP_VALUE = "temp_color"

_LOGGER = logging.getLogger(__name__)

# other helpers
# def get_device_class(hass: HomeAssistant, entity_id: str)
# def get_capability(hass: HomeAssistant, entity_id: str, capability: str)
# def get_supported_features(hass: HomeAssistant, entity_id: str) -> int
# def get_unit_of_measurement(hass: HomeAssistant, entity_id: str) -> str | None:


class HandleLight(Handler):
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.valueList: dict[str, dict[str, Value]] = {}
        self.enableConfigDebug = False
        self.enableEventDebug = False

    def convert_rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def createRgbValue(self, device: Device, entity_id: str, state: State):
        # # Lists attribute color values
        # ATTR_RGB_COLOR = "rgb_color" only one supported at the moment
        # ATTR_RGBW_COLOR = "rgbw_color"
        # ATTR_RGBWW_COLOR = "rgbww_color"
        # ATTR_XY_COLOR = "xy_color"
        # ATTR_HS_COLOR = "hs_color"

        rgb_color = state.attributes.get("rgb_color")

        modes = state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)
        if modes and ColorMode.XY in modes:
            self.valueList[entity_id][COLOR_VALUE] = device.createBlobValue(
                name=entity_id + " color",
                type="color",
                permission=wappstoiot.PermissionType.READWRITE,
                max=10,
                encoding="hex",
                period="0",
                delta="0.0",
            )
        else:
            _LOGGER.warning("Entiry [%s] has no support for color")
            return

        if rgb_color is None:
            rgb_color = (0, 0, 0)

        def setControl(value, data):
            rgb_tuple = struct.unpack("BBB", bytes.fromhex(data))
            service_data = {
                "entity_id": entity_id,
                "rgb_color": rgb_tuple,
            }
            self.hass.services.call(
                domain="light",
                service=SERVICE_TURN_ON,
                service_data=service_data,
                blocking=False,
            )

        self.valueList[entity_id][COLOR_VALUE].report(
            self.convert_rgb_to_hex(rgb_color)
        )
        self.valueList[entity_id][COLOR_VALUE].control(
            self.convert_rgb_to_hex(rgb_color)
        )
        self.valueList[entity_id][COLOR_VALUE].onControl(callback=setControl)

    def createColorTempValue(self, device: Device, entity_id: str, state: State):
        # # ATTR_COLOR_TEMP = "color_temp"  # Deprecated in HA Core 2022.11
        # # ATTR_KELVIN = "kelvin"  # Deprecated in HA Core 2022.11
        # # ATTR_MIN_MIREDS = "min_mireds"  # Deprecated in HA Core 2022.11
        # # ATTR_MAX_MIREDS = "max_mireds"  # Deprecated in HA Core 2022.11
        # ATTR_COLOR_TEMP_KELVIN = "color_temp_kelvin"
        # ATTR_MIN_COLOR_TEMP_KELVIN = "min_color_temp_kelvin"
        # ATTR_MAX_COLOR_TEMP_KELVIN = "max_color_temp_kelvin"

        temp_start = 0

        modes = state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)
        if modes is None or ColorMode.COLOR_TEMP not in modes:
            return

        if (state.attributes.get("min_color_temp_kelvin") is not None) and (
            state.attributes.get("max_color_temp_kelvin") is not None
        ):
            if state.attributes.get("color_temp_kelvin") is not None:
                temp_start = state.attributes.get("color_temp_kelvin")

            minKelvin = state.attributes.get("min_color_temp_kelvin")
            maxKelvin = state.attributes.get("max_color_temp_kelvin")
            self.valueList[entity_id][COLOR_TEMP_VALUE] = device.createNumberValue(
                name="temp Kelvin " + entity_id,
                permission=wappstoiot.PermissionType.READWRITE,
                type="color_temperature",
                min=int(minKelvin) if minKelvin else 0,
                max=int(maxKelvin) if maxKelvin else 0,
                step=1,
                unit="kelvin",
                period="0",
                delta="0.0",
            )

            def setControl(value, data):
                service_data = {
                    "entity_id": entity_id,
                    "color_temp_kelvin": data,
                }
                self.hass.services.call(
                    domain="light",
                    service=SERVICE_TURN_ON,
                    service_data=service_data,
                    blocking=False,
                )

            self.valueList[entity_id][COLOR_TEMP_VALUE].control(temp_start)
            self.valueList[entity_id][COLOR_TEMP_VALUE].report(temp_start)
            self.valueList[entity_id][COLOR_TEMP_VALUE].onControl(callback=setControl)

        elif state.attributes.get("color_temp"):
            if state.attributes.get("min_mireds") and state.attributes.get(
                "max_mireds"
            ):
                minReds = state.attributes.get("min_mireds")
                maxReds = state.attributes.get("max_mireds")
                self.valueList[entity_id][COLOR_TEMP_VALUE] = device.createNumberValue(
                    name="temp mireds " + entity_id,
                    permission=wappstoiot.PermissionType.READWRITE,
                    type="color_temperature",
                    min=int(minReds) if minReds else 0,
                    max=int(maxReds) if maxReds else 0,
                    step=1,
                    unit="mireds",
                    period="0",
                    delta="0.0",
                )

    def createBrightnessValue(self, device: Device, entity_id: str, state: State):
        # # Brightness of the light, 0..255 or percentage
        # ATTR_BRIGHTNESS = "brightness"
        # ATTR_BRIGHTNESS_PCT = "brightness_pct"
        # ATTR_BRIGHTNESS_STEP = "brightness_step"
        # ATTR_BRIGHTNESS_STEP_PCT = "brightness_step_pct"
        max_length = 0
        start_brightness = 0

        if state.attributes.get("brightness"):
            # Create 0-255 brightness
            max_length = 255
            start_brightness = state.attributes.get("brightness")
        elif state.attributes.get("brightness_pct"):
            # Create 0-100 brightness
            max_length = 100
            start_brightness = state.attributes.get("brightness_pct")
        else:
            modes = state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)
            if modes and (
                ColorMode.BRIGHTNESS in modes
                or ColorMode.COLOR_TEMP in modes
                or ColorMode.XY in modes
            ):
                max_length = 255

        if max_length > 0:

            def setControl(value, data):
                service_data = {
                    "entity_id": entity_id,
                }
                if data > 0:
                    service_data["brightness"] = data
                self.hass.services.call(
                    domain="light",
                    service=SERVICE_TURN_OFF if data == 0 else SERVICE_TURN_ON,
                    service_data=service_data,
                    blocking=False,
                )

            self.valueList[entity_id][BRIGHTNESS_VALUE] = device.createNumberValue(
                name=entity_id + " brightness",
                permission=wappstoiot.PermissionType.READWRITE,
                type="brightness",
                min=0,
                max=max_length,
                step=1,
                unit="",
                period="0",
                delta="0.0",
            )
            self.valueList[entity_id][BRIGHTNESS_VALUE].report(start_brightness)
            self.valueList[entity_id][BRIGHTNESS_VALUE].control(start_brightness)
            self.valueList[entity_id][BRIGHTNESS_VALUE].onControl(callback=setControl)

    def createValue(
        self, device: Device, domain: str, entity_id: str, initial_data: str | None
    ) -> None:
        state = self.hass.states.get(entity_id)

        self.valueList[entity_id] = {}

        if self.enableConfigDebug:
            config_name = entity_id + " config"
            tmpConfigValue = device.createStringValue(
                name=config_name,
                type="config",
                permission=wappstoiot.PermissionType.READ,
                max=500,
            )
        else:
            tmpConfigValue = None

        if state:
            if self.enableConfigDebug and tmpConfigValue is not None:
                tmpConfigValue.report(str(state))

            self.createRgbValue(device, entity_id, state)
            self.createColorTempValue(device, entity_id, state)
            self.createBrightnessValue(device, entity_id, state)
        else:
            if self.enableConfigDebug and tmpConfigValue is not None:
                tmpConfigValue.report("No state found")

        if self.enableEventDebug:
            self.valueList[entity_id]["debug"] = device.createStringValue(
                name=entity_id + " debug",
                type="debug",
                permission=wappstoiot.PermissionType.READ,
                max=500,
            )

        self.valueList[entity_id][ONOFF_VALUE] = device.createNumberValue(
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
                # "rgb_color": event.data.get("rgb_color", [255, 255, 255]),
                # "brightness": 255
            }
            self.hass.services.call(
                domain="light",
                service=SERVICE_TURN_ON if data == 1 else SERVICE_TURN_OFF,
                service_data=service_data,
                blocking=False,
            )

        if initial_data:
            self.valueList[entity_id][ONOFF_VALUE].report(
                "1" if initial_data == "on" else "0"
            )
            self.valueList[entity_id][ONOFF_VALUE].control(
                "1" if initial_data == "on" else "0"
            )
        self.valueList[entity_id][ONOFF_VALUE].onControl(callback=setControl)

    def getReport(self, domain: str, entity_id: str, data: str, event: Event) -> None:
        if entity_id not in self.valueList:
            return

        _LOGGER.warning("Testing light event: [%s]", entity_id)

        ## Update onoff, must exist
        if self.valueList[entity_id][ONOFF_VALUE]:
            self.valueList[entity_id][ONOFF_VALUE].report("1" if data == "on" else "0")

        if self.enableEventDebug:
            self.valueList[entity_id]["debug"].report(str(event))

        new_state = event.data.get("new_state")
        if new_state is None:
            _LOGGER.warning("No state data in event!")
            return

        ## Update brightness if exist
        if self.valueList[entity_id].get(
            BRIGHTNESS_VALUE
        ) is not None and new_state.attributes.get("brightness"):
            _LOGGER.warning(
                "Testing light brightness: [%s]",
                new_state.attributes.get("brightness"),
            )

            self.valueList[entity_id][BRIGHTNESS_VALUE].report(
                new_state.attributes.get("brightness")
            )

        ## Update color temperature if exist
        temp_color = new_state.attributes.get("color_temp_kelvin")
        if (
            self.valueList[entity_id].get(COLOR_TEMP_VALUE) is not None
            and temp_color is not None
        ):
            self.valueList[entity_id][COLOR_TEMP_VALUE].report(temp_color)

        ## Update color if exist
        rgb_color = new_state.attributes.get("rgb_color")
        if (
            self.valueList[entity_id].get(COLOR_VALUE) is not None
            and rgb_color is not None
        ):
            self.valueList[entity_id][COLOR_VALUE].report(
                self.convert_rgb_to_hex(rgb_color)
            )

    def removeValue(self, entity_id: str) -> None:
        if entity_id in self.valueList:
            for value in self.valueList[entity_id].values():
                value.delete()
            del self.valueList[entity_id]
