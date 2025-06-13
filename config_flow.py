from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

class SwitchLightConfigFlow(config_entries.ConfigFlow, domain="switch-light"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["light_name"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("light_name"): str,
                vol.Required("switch_entity"): str,
                vol.Required("light_entity"): str,
            })
        )