import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_UUID,
    CONF_EMAIL,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from . import WappstoApi
from .const import (
    DOMAIN,
    ENTITY_LIST,
    SUPPORTED_DOMAINS,
    WAPPSTO_HAS_BEEN_SETUP,
    CA_CRT_KEY,
    CLIENT_CRT_KEY,
    CLIENT_KEY_KEY, SESSION_KEY,
)
from .setup_network import (
    get_session,
    create_network,
    claim_network,
    create_certificaties_files_if_not_exist,
)

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

NETWORK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, str]:
    session = await hass.async_add_executor_job(
        get_session,
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
    )
    if not session:
        raise InvalidLogin

    _LOGGER.error("WHAT IS SESSION: %s", session)

    creator = await hass.async_add_executor_job(create_network, session)

    if not creator:
        raise CouldNotCreate

    network_uuid = creator.get("network", {}).get("id")
    data[CONF_UUID] = network_uuid
    data[CONF_PASSWORD] = ""

    await hass.async_add_executor_job(
        claim_network,
        session,
        network_uuid,
    )
    _LOGGER.warning("Created Network uuid: %s", network_uuid)

    saved_files = await hass.async_add_executor_job(
        create_certificaties_files_if_not_exist, creator
    )
    if not saved_files:
        raise CouldNotCreate

    return {
        SESSION_KEY: session,
        CONF_UUID: network_uuid,
        CA_CRT_KEY: creator["ca"],
        CLIENT_CRT_KEY: creator["certificate"],
        CLIENT_KEY_KEY: creator["private_key"],
    }


class WappstoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        _LOGGER.warning("Init ConfigFLow")

    async def async_step_user(self, user_input):
        errors = {}

        await self.async_set_unique_id(WAPPSTO_HAS_BEEN_SETUP)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                user_input[SESSION_KEY] = info[SESSION_KEY]
                user_input[CA_CRT_KEY] = info[CA_CRT_KEY]
                user_input[CLIENT_CRT_KEY] = info[CLIENT_CRT_KEY]
                user_input[CLIENT_KEY_KEY] = info[CLIENT_KEY_KEY]
                return self.async_create_entry(
                    title="Network: " + info[CONF_UUID],
                    data=user_input,
                    options={ENTITY_LIST: list()},
                )
            except InvalidLogin:
                errors[CONF_EMAIL] = "cannot_connect"
            except CouldNotCreate:
                errors[CONF_EMAIL] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=NETWORK_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
            config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class InvalidLogin(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid username/password."""


class CouldNotCreate(exceptions.HomeAssistantError):
    """Error to indicate culd not create network."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.options = dict(config_entry.options)

    async def async_step_init(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["import_devices", "export_entities"],
        )

    async def async_step_import_devices(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle importing devices from Wappsto."""
        api: WappstoApi  = self.hass.data[DOMAIN][self.config_entry.entry_id]["from_wappsto"]

        if user_input is not None:
            existing_devices = self.options.get("import_devices", [])
            newly_selected = user_input.get("devices_to_add", [])
            self.options["import_devices"] = list(set(existing_devices + newly_selected))
            return await self._update_options()

        all_wappsto_devices = await api.get_devices()
        configured_device_ids = self.options.get("import_devices", [])

        discoverable_devices = {
            dev_id: dev.name
            for dev_id, dev in all_wappsto_devices.items()
            if dev_id not in configured_device_ids
        }

        if not discoverable_devices:
            return self.async_abort(reason="no_new_devices")

        return self.async_show_form(
            step_id="import_devices",
            data_schema=vol.Schema(
                {
                    vol.Optional("devices_to_add"): cv.multi_select(discoverable_devices),
                }
            ),
        )

    async def async_step_export_entities(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the export of entities."""
        entity_id_list = {}
        for state in self.hass.states.async_all():
            (entity_type, dontcare) = state.entity_id.split(".")
            if entity_type in SUPPORTED_DOMAINS:
                entity_id_list[state.entity_id] = state.entity_id

        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="export_entities",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ENTITY_LIST,
                        default=list(self.options.get(ENTITY_LIST, [])),
                    ): cv.multi_select(sorted(entity_id_list)),
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_UUID), data=self.options
        )
