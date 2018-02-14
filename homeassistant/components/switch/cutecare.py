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
from homeassistant.const import (CONF_NAME, CONF_MAC, STATE_OFF, STATE_ON)

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['cutecare']
CONF_THRESHOLD = 'threshold'

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_THRESHOLD, default=1): cv.positive_int
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Setup devices as switches """

    add_devices([CuteCareSwitchProxy(hass, config.get(CONF_MAC), config.get(CONF_NAME), config.get(CONF_THRESHOLD))])


class CuteCareSwitchProxy(JDY08Device, SwitchDevice):
    def __init__(self, hass, mac, name, threshold):
        self._name = name
        self._threshold = threshold
        JDY08Device.__init__(self, hass, mac)

    @property
    def assumed_state(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        _LOGGER.info('Switch value changed to %d, threshold is %d' % (self.major, self._threshold))
        return self.major > self._threshold

    def turn_on(self, **kwargs):
        self._major = 1
        self.set_gpio(2, True)
        self.set_gpio(1, True)
        self.set_gpio(2, True)
        self.set_gpio(1, True)
        self._major = 1

    def turn_off(self, **kwargs):
        self._major = 0
        self.set_gpio(2, False)
        self.set_gpio(1, False)
        self.set_gpio(2, False)
        self.set_gpio(1, False)
        self._major = 0
