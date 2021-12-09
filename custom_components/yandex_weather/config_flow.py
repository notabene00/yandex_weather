from voluptuous import Schema, Required, Optional
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, CONN_CLASS_CLOUD_POLL, HANDLERS
from homeassistant.const import CONF_NAME, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from .weather import DEFAULT_NAME
from . import DOMAIN


@HANDLERS.register(DOMAIN)
class YaWeatherConfigFlow(ConfigFlow):

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input={}, errors={}):
        if user_input:
            await self.async_set_unique_id(
                user_input[CONF_LATITUDE] + user_input[CONF_LONGITUDE]
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input
            )
        SCHEMA = Schema({
            Required(CONF_NAME, default=DEFAULT_NAME): str,
            Required(CONF_API_KEY): str,
            Optional(CONF_LATITUDE, default=self.hass.config.latitude): float,
            Optional(CONF_LONGITUDE, default=self.hass.config.longitude): float
        })
        return self.async_show_form(
            step_id="user", data_schema=SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        self.config = dict(config_entry.data)

    async def async_step_init(self, user_input={}, errors={}):
        """Manage the options."""
        if user_input:
            return self.async_create_entry(title=self.config[CONF_NAME], data=user_input)
        SCHEMA = Schema({
            Required(CONF_NAME, default=self.config[CONF_NAME]): str,
            Required(CONF_API_KEY, default=self.config[CONF_API_KEY]): str,
            Optional(CONF_LATITUDE, default=self.config[CONF_LATITUDE]): float,
            Optional(CONF_LONGITUDE, default=self.config[CONF_LONGITUDE]): float
        })
        return self.async_show_form(
            step_id="user", data_schema=SCHEMA, errors=errors
        )
