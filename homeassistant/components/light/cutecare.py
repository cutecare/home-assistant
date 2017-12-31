"""
Functionality to use a ZigBee device as a light.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.zigbee/
"""
import voluptuous as vol
from homeassistant.components.light import Light
from homeassistant.const import (CONF_NAME, CONF_MAC)

REQUIREMENTS = ['cutecare-py']

CONF_ON_STATE = 'on_state'
DEFAULT_ON_STATE = 'low'
STATES = ['high', 'low']
CONF_DEVICE = 'device'
STATE_FILE_PATH = '/config/cutecare-light-state'

def setup_platform(hass, config, add_devices, discovery_info=None):
    from cutecare.gpio import CuteCareGPIOJDY8
    from cutecare.backends.gatttool import GatttoolBackend

    poller = CuteCareGPIOJDY8(config.get(CONF_MAC), backend=GatttoolBackend, adapter=config.get(CONF_DEVICE))
    add_devices([CuteCareLightProxy(poller, config.get(CONF_NAME))])

class CuteCareLightProxy(Light):
    """Representation of a GPIO pin configured as a digital input."""

    def __init__(self, poller, name):
        self.poller = poller
        self._state = False
        self._name = name

    @property
    def is_on(self):
        """Return True if the Entity is on, else False."""
        return self._state

    @property
    def should_poll(self):
        return True

    @property
    def assumed_state(self):
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def set_state(self, state):
        """Initialize digital out device."""
        self._state = state
        self.poller.set_gpio(1, state)
        file = open(STATE_FILE_PATH, 'w')
        file.write('1' if state else '0')
        file.close()

    def turn_on(self, **kwargs):
        """Set the digital output to its 'on' state."""
        self.set_state(True)

    def turn_off(self, **kwargs):
        """Set the digital output to its 'off' state."""
        self.set_state(False)

    def update(self):
        """Synchronise internal state with the actual light state."""
        file = open(STATE_FILE_PATH, 'r')
        self._state = True if file.read() == '1' else False
        file.close()
