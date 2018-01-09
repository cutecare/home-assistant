"""
Support for CuteCare components.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/cutecare/
"""
import asyncio
from collections import defaultdict
import functools as ft
import logging 
import os

from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP, STATE_UNKNOWN)
from homeassistant.core import CoreState, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.deprecation import get_deprecated
from homeassistant.helpers.entity import Entity
import voluptuous as vol
from bluepy.btle import Scanner, DefaultDelegate

REQUIREMENTS = ['cutecare-py']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'cutecare'
CUTECARE_DEVICES = 'devices'
CUTECARE_STATE = 'state'

@asyncio.coroutine
def async_setup(hass, config):
    """Set up the CuteCare component."""

    # Allow entities to register themselves by mac address to be looked up
    # when processing events
    hass.data[DOMAIN] = {
        CUTECARE_DEVICES: defaultdict(list),
        CUTECARE_STATE: True
    }

    @asyncio.coroutine
    def scan_ble_devices():
        """Scanning BLE devices."""
        _LOGGER.info('Start scanning of BLE devices')

        # handle shutdown
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, stop_scanning)

        scanner = Scanner(0).withDelegate(BLEScanDelegate(hass))
        while hass.data[DOMAIN][CUTECARE_STATE]:
            try:
                scanner.scan(1.0)
            except bluepy.btle.BTLEException as e:
                _LOGGER.error(e)

        _LOGGER.info('Scanning has been terminated')

    def stop_scanning(event):
        __LOGGER.info('Stop scanning BLE devices')
        hass.data[DOMAIN][CUTECARE_STATE] = False

    hass.async_add_job(scan_ble_devices)
    return True

class BLEScanDelegate(DefaultDelegate):
    def __init__(self, hass):
        self._hass = hass
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr in self._hass.data[DOMAIN][CUTECARE_DEVICES]:
            entity = self._hass.data[DOMAIN][CUTECARE_DEVICES][dev.addr]
            for (adtype, value) in dev.getScanData():
                if adtype == 22:
                    _LOGGER.info('BLE device service message has been found %s' % (value))
                    entity.set_data(value)


class CuteCareDevice(Entity):
    """Common logic of a CuteCare device."""

    def __init__(self, hass, mac):
        """Initialize the device."""
        self.hass = hass
        self.mac = mac
        self.hass.data[DOMAIN][CUTECARE_DEVICES][mac] = self


class JDY08Device(CuteCareDevice):
    def __init__(self, hass, mac):
        self._major = 0
        self._minor = 0
        self._temp = 0
        self._humidity = 0
        self._battery = 0
        CuteCareDevice.__init__(self, hass, mac)

    @property
    def should_poll(self):
        return False

    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def temperature(self):
        return self._temp

    @property
    def humidity(self):
        return self._humidity

    @property
    def battery(self):
        return self._battery

    def set_data(self, data):
        """Parse service data."""
        segments = list(map(''.join, zip(*[iter(data)]*4)))
        self._major = int(segments[3], 16)
        self._minor = int(segments[4], 16)
        self._temp = int(segments[6], 16) >> 8
        self._humidity = int(segments[6], 16) & 0xFF
        self._battery = int(segments[7], 16)
