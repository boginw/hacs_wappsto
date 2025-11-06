import logging
import requests
import json
import asyncio
import aiohttp
import websockets
import ssl
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .wappsto_device import WappstoDevice, WappstoValue

_LOGGER = logging.getLogger(__name__)


class WappstoApi:
    """API for fetching devices from Wappsto."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the API."""
        self.hass = hass
        self.entry = entry
        self.session = entry.data["session"]
        self.wappsto_devices: dict[str, WappstoDevice] = {}
        self._update_callbacks: dict[str, list] = {}
        self.websocket_task = None

    async def get_devices(self) -> dict[str, WappstoDevice]:
        """Fetch Wappsto devices and values."""

        url = "https://wappsto.com/services/2.1/network?expand=2"
        headers = {"X-session": self.session}
        devices = {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                response = await resp.json()
                for network in response:
                    for device in network["device"]:
                        device_id = device["meta"]["id"]
                        devices[device_id] = WappstoDevice(
                            wappsto_id=device_id,
                            name=network["meta"]["name_by_user"] + " - " + device["meta"]["name_by_user"],
                            values={},
                        )

        return devices

    async def get_device(self, device_id) -> WappstoDevice:
        """Fetch Wappsto devices and values."""

        url = f"https://wappsto.com/services/2.1/device/{device_id}?expand=2"
        headers = {"X-session": self.session}

        async with aiohttp.ClientSession() as session:
            _LOGGER.warning("Fetching Wappsto Device: " + device_id + "")
            async with session.get(url, headers=headers) as resp:
                device_data = await resp.json()
                device = WappstoDevice(
                    wappsto_id=device_id,
                    name=device_data["meta"]["parent_name_by_user"]["network"] + " - " + device_data["meta"]["name_by_user"],
                    values={},
                )

                for value_data in device_data.get("value", []):
                    if isinstance(value_data, str):
                        _LOGGER.warning("Value ID was a string: %s, had to fetch value", value_data)
                        value_id = value_data
                        url = f"https://wappsto.com/services/2.1/value/{value_id}?expand=2"
                        headers = {"X-session": self.session}
                        response = await session.get(url, headers=headers)
                        value_data = await response.json()
                    else:
                        value_id = value_data["meta"]["id"]

                    if value_data is None or "meta" not in value_data or "id" not in value_data["meta"]:
                        raise ValueError("Value has no ID: " + json.dumps(value_data))

                    state_read = None
                    state_write = None
                    report_data = ""
                    for state_data in value_data.get("state", []):
                        if state_data.get("type") == "Report":
                            report_data = state_data.get("data", "")
                            state_read = state_data.get("meta", {}).get("id")
                        elif state_data.get("type") == "Control":
                            state_write = state_data.get("meta", {}).get("id")

                    value = WappstoValue(
                        wappsto_id=value_id,
                        name=value_data["name"],
                        type=value_data["type"],
                        permission=value_data["permission"],
                        data=report_data,
                        unit=value_data.get("number", {}).get("unit"),
                        state_read=state_read,
                        state_write=state_write,
                    )
                    device.values[value_id] = value

                self.wappsto_devices[device_id] = device
                return device

    def get_devices_deep(self) -> dict[str, WappstoDevice]:
        """Fetch Wappsto devices and values."""

        _LOGGER.warning("Fetching Wappsto devices")

        url = "https://wappsto.com/services/2.1/network?expand=0"
        headers = {"X-session": self.session}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        networks = response.json()

        for network in networks:
            network_id = network["meta"]["id"]
            _LOGGER.warning("Fetching Wappsto network: " + network_id + "")

            url = f"https://wappsto.com/services/2.1/network/{network_id}?expand=10"
            headers = {"X-session": self.session}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            network = response.json()

            for device_data in network.get("device", []):
                device_id = device_data["meta"]["id"]
                device = WappstoDevice(
                    wappsto_id=device_id,
                    name=device_data["name"],
                    values={},
                )
                self.wappsto_devices[device_id] = device

                _LOGGER.warning("Fetching Wappsto device: " + device_id + "")
                url = f"https://wappsto.com/services/2.1/device/{device_id}?expand=10"
                headers = {"X-session": self.session}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                device_data = response.json()

                for value_data in device_data.get("value", []):
                    if isinstance(value_data, str):
                        _LOGGER.warning("Value ID was a string: %s, had to fetch value", value_data)
                        value_id = value_data
                        url = f"https://wappsto.com/services/2.1/value/{value_id}?expand=10"
                        headers = {"X-session": self.session}
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        value_data = response.json()
                    else:
                        value_id = value_data["meta"]["id"]

                    if value_data is None or "meta" not in value_data or "id" not in value_data["meta"]:
                        raise ValueError(
                            "Value has no ID: " + json.dumps(value_data) + " in network " + json.dumps(network))

                    data = ""
                    for state_data in value_data.get("state", []):
                        if value_data["type"] == "Report":
                            data = state_data["data"]
                            break

                    value = WappstoValue(
                        wappsto_id=value_id,
                        name=value_data["name"],
                        type=value_data["type"],
                        permission=value_data["permission"],
                        data=data,
                        unit=value_data.get("number", {}).get("unit"),
                    )
                    device.values[value_id] = value

        _LOGGER.warning("Done fetching Wappsto devices")

        return self.wappsto_devices

    async def start_websocket(self):
        """Start the WebSocket connection."""
        url = f"wss://wappsto.com/services/2.1/websocket/open?X-Session={self.session}&subscription=[/network]"
        ssl_context = await self.hass.async_add_executor_job(ssl.create_default_context)
        while True:
            try:
                async with websockets.connect(url, ssl=ssl_context) as websocket:
                    _LOGGER.info("Connected to Wappsto WebSocket")
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("event") == "update" and data.get("data"):
                            if data["data"].get("data") is None:
                                continue

                            new_data = data["data"]["data"]
                            # /network/<network-id>/device/<device-id>/value/<value-id>/state/<state-id>
                            value_id = data["path"].split("/")[6]
                            self._on_wappsto_update(value_id, new_data)
            except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError):
                _LOGGER.warning("Wappsto WebSocket connection lost. Reconnecting in 10 seconds.")
                await asyncio.sleep(10)

    def _on_wappsto_update(self, value_id, data):
        """Handle update from Wappsto."""
        _LOGGER.warning("Received update for %s: %s", value_id, data)
        for device in self.wappsto_devices.values():
            if value := device.get_value(value_id):
                value.data = data
                if value_id in self._update_callbacks:
                    for callback in self._update_callbacks[value_id]:
                        callback()
                break

    def register_update_callback(self, value_id: str, callback) -> None:
        """Register a callback for value updates."""
        if value_id not in self._update_callbacks:
            self._update_callbacks[value_id] = []
        self._update_callbacks[value_id].append(callback)

    def unregister_update_callback(self, value_id: str, callback) -> None:
        """Unregister a callback for value updates."""
        if value_id in self._update_callbacks and callback in self._update_callbacks[value_id]:
            self._update_callbacks[value_id].remove(callback)

    async def send_command(self, value: WappstoValue, data: str) -> None:
        """Send a command to a Wappsto device."""
        url = f"https://wappsto.com/services/2.1/state/{value.state_write}"
        headers = {"X-session": self.session, "Content-Type": "application/json"}
        payload = {"data": data}

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()

                if resp.status == 200:
                    _LOGGER.warning("Command sent successfully to %s", value.wappsto_id)
                    self._on_wappsto_update(value.wappsto_id, data)
                else:
                    _LOGGER.error(
                        "Failed to send command to %s: %s", value.wappsto_id, await resp.text()
                    )
