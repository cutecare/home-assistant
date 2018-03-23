"""
Support for CuteCare BLE universal sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.cutecare/
"""
import logging
import voluptuous as vol

from homeassistant.components.cutecare import CC41ADevice, JDY10Device, JDY08Device
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_TYPE, CONF_MAC)

DEPENDENCIES = ['cutecare']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'CuteCare Sensor'
SENSOR_TYPES = {
    'dryness': ['Dryness', '%'],
    'moisture': ['Moisture', '%.'],
    'temperature': ['Temperature', 'C'],
    'pressure': ['Pressure', 'mm/hg'],
    'co2': ['CO2', 'ppm'],
    'watt': ['Power', 'W'],
    'lux': ['Illuminance', 'lux']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_TYPE, default="jdy8"): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=SENSOR_TYPES): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})

def setup_platform(hass, config, add_devices, discovery_info=None):

    devs = []
    for parameter in config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][0]
        unit = SENSOR_TYPES[parameter][1]
        prefix = config.get(CONF_NAME)
        if prefix:
            name = "{} {}".format(prefix, name)
        
        if config.get(CONF_TYPE) == 'jdy10':
            devs.append(CuteCareJDY10SensorProxy(hass, config.get(CONF_MAC), name, unit))
        elif config.get(CONF_TYPE) == 'jdy8':
            devs.append(CuteCareJDY8SensorProxy(hass, config.get(CONF_MAC), name, unit))
        else:
            devs.append(CuteCareSensorProxy(hass, config.get(CONF_MAC), name, unit))

    add_devices(devs)

class CuteCareSensorProxy(CC41ADevice):
    def __init__(self, hass, mac, name, unit):
        self._unit = unit
        self._name = name
        self._force_update = False
        self._state = None
        CC41ADevice.__init__(self, hass, mac)

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

        transformations = {
            '%': lambda value: round((value / 1024) * 100,1),
            '%.': lambda value: round(100 - (value / 1024) * 100,1),
            'lux': lambda value: value,
            'W': lambda value: value
        }
        self._state = transformations[self._unit](self.value)


class CuteCareJDY10SensorProxy(JDY10Device):
    def __init__(self, hass, mac, name, unit):
        self._unit = unit
        self._name = name
        self._force_update = False
        self._state = None
        JDY10Device.__init__(self, hass, mac)

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

        transformations = {
            'C': self.valueLow,
            'mm/hg': self.valueHigh,
            'ppm': self.valueHigh * 10
        }
        self._state = transformations[self._unit]        


class CuteCareJDY8SensorProxy(JDY08Device):
    def __init__(self, hass, mac, name, unit):
        self._unit = unit
        self._name = name
        self._force_update = False
        self._state = None
        JDY08Device.__init__(self, hass, mac)

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

        transformations = {
            '%': 100 - self.humidity,
            '%.': self.humidity,
            'C': self.temperature,
            'ppm': self.major,
            'W': self.major,
            'lux': self.major,
            'mm/hg': self.minor
        }
        self._state = transformations[self._unit]                