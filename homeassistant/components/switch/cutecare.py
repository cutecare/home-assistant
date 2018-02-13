"""
Binary sensor on CuteCate platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.cutecare/
"""
from homeassistant.components.cutecare import JDY08Device
from homeassistant.components.switch import SwitchDevice
from homeassistant.const import (CONF_NAME, CONF_MAC, STATE_OFF, STATE_ON)

DEPENDENCIES = ['cutecare']

def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Setup devices as switches """

    add_devices([CuteCareSwitchProxy(hass, config.get(CONF_MAC), config.get(CONF_NAME))])


class CuteCareSwitchProxy(JDY08Device, SwitchDevice):
    def __init__(self, hass, mac, name):
        self._name = name
        JDY08Device.__init__(self, hass, mac)

    @property
    def assumed_state(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self.major > 0

    def turn_on(self, **kwargs):
        self.set_gpio(1, True)
        self.set_gpio(2, True)

    def turn_off(self, **kwargs):
        self.set_gpio(1, False)
        self.set_gpio(2, False)
