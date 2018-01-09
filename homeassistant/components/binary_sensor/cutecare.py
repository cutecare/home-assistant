"""
Binary sensor on CuteCate platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.cutecare/
"""
from homeassistant.components.cutecare import JDY08Device
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import (CONF_NAME, CONF_MAC)

DEPENDENCIES = ['cutecare']

def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Setup devices as binary sensors """

    add_devices([CuteCareBinarySensorProxy(hass, config.get(CONF_MAC), config.get(CONF_NAME))])


class CuteCareBinarySensorProxy(JDY08Device, BinarySensorDevice):
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
