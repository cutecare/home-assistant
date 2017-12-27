"""
Support for CuteCare BLE universal sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.cutecare/
"""
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_MAC)

REQUIREMENTS = ['cutecare-py']

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE = 'device'
CONF_CACHE = 'cache_value'
CONF_RETRIES = 'retries'
CONF_TIMEOUT = 'timeout'

DEFAULT_DEVICE = 'hci0'
DEFAULT_UPDATE_INTERVAL = 1200
DEFAULT_NAME = 'CuteCare Sensor'
DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 5

SENSOR_TYPES = {
    'Moisture': ['Moisture', '%']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=SENSOR_TYPES): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
    vol.Optional(CONF_CACHE, default=DEFAULT_UPDATE_INTERVAL): cv.positive_int,
    vol.Optional(CONF_DEVICE, default=DEFAULT_DEVICE): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    from cutecare.poller import CuteCarePollerCC41A
    from cutecare.backends.gatttool import GatttoolBackend

    cache = config.get(CONF_CACHE)
    devs = []

    poller = CuteCarePollerCC41A(config.get(CONF_MAC), backend=GatttoolBackend, adapter=config.get(CONF_DEVICE))
    poller.ble_timeout = config.get(CONF_TIMEOUT)
    poller.retries = config.get(CONF_RETRIES)

    for parameter in config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][0]
        unit = SENSOR_TYPES[parameter][1]
        prefix = config.get(CONF_NAME)
        if prefix:
            name = "{} {}".format(prefix, name)
        devs.append(CuteCareSensorProxy(poller, name, unit))

    add_devices(devs)

class CuteCareSensorProxy(Entity):
    def __init__(self, poller, name, unit):
        self.poller = poller
        self._unit = unit
        self._name = name
        self._force_update = False
        self._state = None
        self.data = []

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    def update(self):
        """ Update sendor conditions. """
        try:
            _LOGGER.debug("Polling data for %s", self.name)
            self._state = self.poller.parameter_value()
        except IOError as ioerr:
            _LOGGER.info("Polling error %s", ioerr)
            self._state = None
