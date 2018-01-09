"""
Binary sensor on CuteCate platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.cutecare/
"""
from homeassistant.components.cutecare import CuteCareJDY08
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import (CONF_NAME, CONF_MAC)

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([CuteCareBinarySensorProxy(hass, config.get(CONF_MAC), config.get(CONF_NAME))])

class CuteCareBinarySensorProxy(BinarySensorDevice, CuteCareJDY08):
    """Representation of a GPIO pin configured as a digital input."""

    def __init__(self, hass, mac, name):
        self._name = name
        CuteCareJDY08.__init__(self, hass, mac)

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
        return self.major() > 0
