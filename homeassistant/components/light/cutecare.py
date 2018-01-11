"""
Functionality to use a ZigBee device as a light.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.zigbee/
"""
from homeassistant.components.cutecare import JDY08Device
from homeassistant.components.light import Light
from homeassistant.const import (CONF_NAME, CONF_MAC)

DEPENDENCIES = ['cutecare']

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([CuteCareLightProxy(hass, config.get(CONF_MAC), config.get(CONF_NAME))])

class CuteCareLightProxy(JDY08Device, Light):
    def __init__(self, hass, mac, name):
        self._name = name
        JDY08Device.__init__(self, hass, mac)

    @property
    def assumed_state(self):
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def turn_on(self, **kwargs):
        """Set the digital output to its 'on' state."""
        self.set_gpio(1, True)

    def turn_off(self, **kwargs):
        """Set the digital output to its 'off' state."""
        self.set_gpio(1, False)
