"""
Binary sensor on CuteCate platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.cutecare/
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.cutecare import (JDY08Device, CC41ADevice)
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_MAC, CONF_TYPE)

DEPENDENCIES = ['cutecare']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_TYPE, default="jdy8"): cv.string,
    vol.Optional(CONF_NAME): cv.string
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    mac = config.get(CONF_MAC)
    if config.get(CONF_TYPE) == 'cc41a':
        add_devices([CuteCareCC41ABinarySensorProxy(hass, mac, name)])
    else:
        add_devices([CuteCareJDY8BinarySensorProxy(hass, mac, name)])


class CuteCareJDY8BinarySensorProxy(JDY08Device, BinarySensorDevice):
    def __init__(self, hass, mac, name):
        self._name = name
        JDY08Device.__init__(self, hass, mac)

    @property
    def assumed_state(self):
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.major > 0


class CuteCareCC41ABinarySensorProxy(CC41ADevice, BinarySensorDevice):
    def __init__(self, hass, mac, name):
        self._name = name
        CC41ADevice.__init__(self, hass, mac)

    @property
    def assumed_state(self):
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.value > 0