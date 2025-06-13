from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.components.light import (
    LightEntity,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_COLOR_MODE,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_XY_COLOR,
    ATTR_HS_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_MIN_COLOR_TEMP_KELVIN,
    ATTR_MAX_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
)
from homeassistant.const import STATE_ON

async def async_setup_entry(hass, config_entry, async_add_entities):
    data = config_entry.data
    async_add_entities([
        DynamicControlledLight(
            hass,
            data["light_name"],
            data["switch_entity"],
            data["light_entity"]
        )
    ])

class DynamicControlledLight(LightEntity):
    def __init__(self, hass, light_name, switch_entity_id, light_entity_id):
        self._hass = hass
        self._light_name = light_name
        self._switch_entity_id = switch_entity_id
        self._light_entity_id = light_entity_id

    @property
    def device_info(self):
        return {
            "identifiers": {(self._hass.domain, f"{self._switch_entity_id}_{self._light_entity_id}")},
            "name": self._light_name,
            "manufacturer": "Elio",
            "model": "Controlled Light",
        }

    @property
    def name(self):
        return self._light_name

    @property
    def icon(self):
        return self._get_light_attr("icon")

    def _get_entity_state(self, entity_id):
        return self._hass.states.get(entity_id)

    def _get_light_attr(self, attr):
        state = self._get_entity_state(self._light_entity_id)
        return state.attributes.get(attr) if state else None

    def _get_switch_attr(self, attr):
        state = self._get_entity_state(self._switch_entity_id)
        return state.attributes.get(attr) if state else None

    @property
    def is_on(self):
        state = self._hass.states.get(self._switch_entity_id)
        return state and state.state == STATE_ON

    @property
    def supported_color_modes(self):
        return self._get_light_attr(ATTR_SUPPORTED_COLOR_MODES)

    @property
    def color_mode(self):
        return self._get_light_attr(ATTR_COLOR_MODE)

    @property
    def brightness(self):
        return self._get_light_attr(ATTR_BRIGHTNESS)

    @property
    def color_temp_kelvin(self):
        return self._get_light_attr(ATTR_COLOR_TEMP_KELVIN)

    @property
    def hs_color(self):
        return self._get_light_attr(ATTR_HS_COLOR)

    @property
    def xy_color(self):
        return self._get_light_attr(ATTR_XY_COLOR)

    @property
    def rgb_color(self):
        return self._get_light_attr(ATTR_RGB_COLOR)

    @property
    def rgbw_color(self):
        return self._get_light_attr(ATTR_RGBW_COLOR)

    @property
    def rgbww_color(self):
        return self._get_light_attr(ATTR_RGBWW_COLOR)

    @property
    def effect(self):
        return self._get_light_attr(ATTR_EFFECT)

    @property
    def effect_list(self):
        return self._get_light_attr(ATTR_EFFECT_LIST)

    @property
    def min_color_temp_kelvin(self):
        return self._get_light_attr(ATTR_MIN_COLOR_TEMP_KELVIN)

    @property
    def max_color_temp_kelvin(self):
        return self._get_light_attr(ATTR_MAX_COLOR_TEMP_KELVIN)

    async def async_turn_on(self, **kwargs):
        await self._hass.services.async_call(
            "switch",
            "turn_on",
            {
                "entity_id": self._switch_entity_id,
            },
            blocking=True
        )
        await self._wait_for_entity_update(self._switch_entity_id)
        await self._hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": self._light_entity_id,
                **kwargs
            },
            blocking=True
        )
        await self._wait_for_entity_update(self._light_entity_id)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._hass.services.async_call(
            "light",
            "turn_off",
            {
                "entity_id": self._light_entity_id
            },
            blocking=True
        )
        await self._wait_for_entity_update(self._light_entity_id)
        await self._hass.services.async_call(
            "switch",
            "turn_off",
            {
                "entity_id": self._switch_entity_id
            },
            blocking=True
        )
        await self._wait_for_entity_update(self._switch_entity_id)
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        if self.is_on:
            await self.async_turn_off(**kwargs)
        else:
            await self.async_turn_on(**kwargs)

    async def _wait_for_entity_update(self, entity_id, timeout=0.5):
        import asyncio
        from datetime import datetime

        old_state = self._get_entity_state(entity_id)
        start = datetime.now()

        while (datetime.now() - start).total_seconds() < timeout:
            await asyncio.sleep(0.1)
            new_state = self._get_entity_state(entity_id)
            if not old_state or not new_state:
                break
            if new_state.state != old_state.state or new_state.attributes != old_state.attributes:
                break

    async def async_added_to_hass(self):
        async def state_change_listener(event):
            entity_id = event.data.get("entity_id")
            if entity_id in [self._switch_entity_id, self._light_entity_id]:
                self.async_write_ha_state()

        self._unsub_state_listener = async_track_state_change_event(
            self._hass,
            [self._switch_entity_id, self._light_entity_id],
            state_change_listener
        )