"""
Functionality to use a ZigBee device as a light.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.zigbee/
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.cutecare import JDY08Device
from homeassistant.components.light import Light
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_MAC)

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['cutecare']
CONF_PIN_NUMBER = 'pin'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_PIN_NUMBER, default=1): cv.positive_int
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([CuteCareLightProxy(hass, config)])

class CuteCareLightProxy(JDY08Device, Light):
    def __init__(self, hass, config):
        self._name = config.get(CONF_NAME)
        self._pin = config.get(CONF_PIN_NUMBER)
        JDY08Device.__init__(self, hass, config.get(CONF_MAC))

    def is_on(self) -> bool:
        raise False

    @property
    def assumed_state(self):
        return True

    @property
    def name(self):
        return self._name

    def turn_on(self, **kwargs):
        self.set_gpio(self._pin, True)

    def turn_off(self, **kwargs):
        self.set_gpio(self._pin, False)
