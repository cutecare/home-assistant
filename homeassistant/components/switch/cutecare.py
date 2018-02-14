"""
Binary sensor on CuteCate platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.cutecare/
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.cutecare import JDY08Device
from homeassistant.components.switch import SwitchDevice
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_MAC, STATE_OFF, STATE_ON)

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['cutecare']
CONF_THRESHOLD = 'threshold'
CONF_PIN_NUMBER = 'pin'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_THRESHOLD, default=1): cv.positive_int,
    vol.Optional(CONF_PIN_NUMBER, default=1): cv.positive_int
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([CuteCareSwitchProxy(hass, config)])


class CuteCareSwitchProxy(JDY08Device, SwitchDevice):
    def __init__(self, hass, config):
        self._name = config.get(CONF_NAME)
        self._threshold = config.get(CONF_THRESHOLD)
        self._pin = config.get(CONF_PIN_NUMBER)
        JDY08Device.__init__(self, hass, config.get(CONF_MAC))

    @property
    def assumed_state(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        _LOGGER.debug('Switch value is %d, threshold is %d' % (self.major, self._threshold))
        return False if self.state_obsolete else (self.major > self._threshold)

    def turn_on(self, **kwargs):
        self.set_gpio(self._pin, True)
        self._major = self._threshold + 1

    def turn_off(self, **kwargs):
        self.set_gpio(self._pin, False)
        self._major = 0
