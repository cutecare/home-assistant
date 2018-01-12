"""
Support for CuteCare components.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/cutecare/
"""
import asyncio
from collections import defaultdict
from datetime import timedelta
import logging 

from homeassistant.const import (EVENT_HOMEASSISTANT_STOP)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from bluepy.btle import Scanner, Peripheral, DefaultDelegate, BTLEException

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'cutecare'
CUTECARE_DEVICES = 'devices'
CUTECARE_STATE = 'state'
CUTECARE_SCAN_TIMES = 'scan-times'
CUTECARE_RESTART = 'restart-flag'

@asyncio.coroutine
def async_setup(hass, config):
    """Set up the CuteCare component."""

    # Allow entities to register themselves by mac address to be looked up
    # when processing events
    hass.data[DOMAIN] = {
        CUTECARE_DEVICES: defaultdict(list),
        CUTECARE_STATE: True,
        CUTECARE_RESTART: False,
        CUTECARE_SCAN_TIMES: 0
    }

    @asyncio.coroutine
    def scan_ble_devices(now):
        """Main loop where BLE devices are scanned."""

        if hass.data[DOMAIN][CUTECARE_STATE]:
            try:
                if hass.data[DOMAIN][CUTECARE_SCAN_TIMES] < 3:
                    hass.data[DOMAIN][CUTECARE_SCAN_TIMES] += 1
                else:
                    hass.data[DOMAIN][CUTECARE_SCAN_TIMES] = 0
                    scanner.clear()
                    scanner.stop()
                    scanner.start()

                scanner.process(1.0)

            except BTLEException as e:
                _LOGGER.error(e)
                try:
                    scanner.start()
                except BTLEException as e:
                    hass.data[DOMAIN][CUTECARE_RESTART] = True
                    _LOGGER.error(e)

        else:
            _LOGGER.info('Scanning has been completed')

    def stop_scanning(event):
        _LOGGER.info('Stop scanning BLE devices')
        hass.data[DOMAIN][CUTECARE_STATE] = False
        scanner.stop()

    def restart_bluetooth(now):
        import os
        if hass.data[DOMAIN][CUTECARE_RESTART]:
            hass.data[DOMAIN][CUTECARE_RESTART] = False
            os.spawnv(os.P_WAIT, "hciconfig", ["hciconfig", "hci0", "down"])
            os.spawnv(os.P_WAIT, "hciconfig", ["hciconfig", "hci0", "up"])
            os.spawnv(os.P_NOWAIT, "/etc/init.d/bluetooth", ["/etc/init.d/bluetooth", "restart"])

    # handle shutdown
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, stop_scanning)

    _LOGGER.info('Start scanning of BLE devices')

    restart_bluetooth()
    scanner = Scanner(0).withDelegate(BLEScanDelegate(hass))
    scanner.start()

    # scan devices periodically
    async_track_time_interval(hass, scan_ble_devices, timedelta(seconds=1))

    # restart bluetooth services if needed
    async_track_time_interval(hass, restart_bluetooth, timedelta(seconds=10))

    return True

class BLEScanDelegate(DefaultDelegate):
    def __init__(self, hass):
        self._hass = hass
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        address = dev.addr.upper()
        if address in self._hass.data[DOMAIN][CUTECARE_DEVICES]:
            entity = self._hass.data[DOMAIN][CUTECARE_DEVICES][address]
            for (adtype, description, value) in dev.getScanData():
                if adtype == 255:
                    _LOGGER.info('BLE device manufacturer has been found %s' % (value))
                    entity.parse_manufacturer_data(value)
                if adtype == 22:
                    _LOGGER.info('BLE device service message has been found %s' % (value))
                    entity.parse_service_data(value)


class CuteCareDevice(Entity):
    """Common logic of a CuteCare device."""

    def __init__(self, hass, mac):
        """Initialize the device."""
        self.hass = hass
        self.mac = mac.upper()
        self.hass.data[DOMAIN][CUTECARE_DEVICES][self.mac] = self


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

    def parse_service_data(self, data):
        """Parse service data."""

        segments = list(map(''.join, zip(*[iter(data)]*2)))
        if len(segments) > 2:
            self._temp = int(segments[-3], 16)
            self._humidity = int(segments[-2], 16)
            self._battery = int(segments[-1], 16)

        segments = list(map(''.join, zip(*[iter(data)]*4)))
        if len(segments) > 4:
            self._major = int(segments[3], 16)
            self._minor = int(segments[4], 16)

        self.schedule_update_ha_state(True)

    def parse_manufacturer_data(self, data):
        """Parse manufacturer data."""

        segments = list(map(''.join, zip(*[iter(data)]*4)))
        if len(segments) > 11:
            self._major = int(segments[10], 16)
            self._minor = int(segments[11], 16)

        self.schedule_update_ha_state(True)

    def set_gpio(self, pin, state):
        
        try:
            device = Peripheral(self.mac)
            onBytes = bytes([231, 240 + pin, 1])
            offBytes = bytes([231, 240 + pin, 0])
            
            attempts = 3
            while attempts > 0:
                device.writeCharacteristic( 7, onBytes if state else offBytes, False)
                attempts -= 1

            device.disconnect()

        except BTLEException as e:
            _LOGGER.error("Unable set GPIO of JDY08: %s" % e)
