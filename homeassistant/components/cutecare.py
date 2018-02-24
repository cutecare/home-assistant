"""
Support for CuteCare components.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/cutecare/
"""
import asyncio
from collections import defaultdict
from threading import Lock, Thread
from datetime import timedelta, datetime
import logging 
from time import sleep

from homeassistant.const import (EVENT_HOMEASSISTANT_STOP, EVENT_STATE_CHANGED)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import now as dt_now
from bluepy.btle import Scanner, Peripheral, DefaultDelegate, BTLEException

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'cutecare'
CUTECARE_DEVICES = 'devices'
CUTECARE_STATE = 'state'
CUTECARE_SCAN_TIMES = 'scan-times'
CUTECARE_DEVICE = 0
CUTECARE_LOCK = 'hci-lock'

@asyncio.coroutine
def async_setup(hass, config):
    """Set up the CuteCare component."""

    # Allow entities to register themselves by mac address to be looked up
    # when processing events
    hass.data[DOMAIN] = {
        CUTECARE_DEVICES: defaultdict(list),
        CUTECARE_STATE: True,
        CUTECARE_LOCK: Lock()
    }

    @asyncio.coroutine
    def scan_ble_devices(now):
        """Main loop where BLE devices are scanned."""

        def scan_thread_func(hass):
            hass.data[DOMAIN][CUTECARE_LOCK].acquire()
            try:
                scanner = Scanner(CUTECARE_DEVICE).withDelegate(BLEScanDelegate(hass))
                scanner.scan(3.0)

            except BTLEException as e:
                _LOGGER.error(e)
                restart_bluetooth()

            finally:
                hass.data[DOMAIN][CUTECARE_LOCK].release()

        if hass.data[DOMAIN][CUTECARE_STATE]:
            t = Thread(target=scan_thread_func, args=(hass,))
            t.start()

    def stop_scanning(event):
        _LOGGER.info('Stop scanning BLE devices')
        hass.data[DOMAIN][CUTECARE_STATE] = False

    def restart_bluetooth():
        import os

        retries = 3
        while retries > 0:
            retries -= 1      
            
            try:
                Scanner(CUTECARE_DEVICE).scan(1.0)
                break

            except BTLEException as e:
                os.system("hciconfig hci" + str(CUTECARE_DEVICE) + " down")
                os.system("hciconfig hci" + str(CUTECARE_DEVICE) + " up")
                os.system("service bluetooth restart")

        _LOGGER.info('Bluetooth services have been restarted')


    # initialize BLE advertising mode
    _LOGGER.info('Start scanning of BLE devices')

    # handle shutdown
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_scanning)

    attempts = 3
    while attempts > 0:
        attempts -= 1

        try:
            scanner = Scanner(CUTECARE_DEVICE).withDelegate(BLEScanDelegate(hass))
            scanner.start()
            scanner.stop()
            break

        except BTLEException as e:
            _LOGGER.error(e)
            restart_bluetooth()

    # look for advertising messages periodically
    async_track_time_interval(hass, scan_ble_devices, timedelta(milliseconds=3200))

    return True

class BLEScanDelegate(DefaultDelegate):
    def __init__(self, hass):
        self._hass = hass
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        address = dev.addr.upper()
        deviceInfo = {
            "mac": address,
            "entity_id": "cutecare.ble_scanner",
            "name": "",
            "friendly_name": ""
        }
        for (adtype, description, value) in dev.getScanData():
            if adtype == 9:
                deviceInfo["friendly_name"] = value

        if address in self._hass.data[DOMAIN][CUTECARE_DEVICES]:
            for entity in self._hass.data[DOMAIN][CUTECARE_DEVICES][address]:
                entity.reset_state_time()
                for (adtype, description, value) in dev.getScanData():
                    # _LOGGER.info('BLE message %d with text %s for %s' % (adtype, value, address))
                    if adtype == 255:
                        _LOGGER.debug('BLE device manufacturer has been found %s' % (value))
                        entity.parse_manufacturer_data(value)
                    if adtype == 22:
                        _LOGGER.debug('BLE device service message has been found %s' % (value))
                        entity.parse_service_data(value)
                    if adtype == 9:
                        deviceInfo["name"] = entity.name
                    if adtype == 2:
                        _LOGGER.debug('BLE device service class UUIDs been found %s' % (value))
                        entity.parse_service_class_data(value)

        if deviceInfo["friendly_name"] != "":
            self._hass.bus.async_fire(EVENT_STATE_CHANGED, deviceInfo)


class CuteCareDevice(Entity):
    """Common logic of a CuteCare device."""

    def __init__(self, hass, mac):
        """Initialize the device."""
        self.hass = hass
        self.mac = mac.upper()
        self.reset_state_time()

        if self.mac not in hass.data[DOMAIN][CUTECARE_DEVICES]:
            hass.data[DOMAIN][CUTECARE_DEVICES][self.mac] = []
        hass.data[DOMAIN][CUTECARE_DEVICES][self.mac].append(self)

    def reset_state_time(self):
        self.update_dt = dt_now()

    @property
    def state_obsolete(self):
        return int(dt_now().timestamp() - self.update_dt.timestamp()) > 600

    def set_friendly_name(self, name):
        self.friendly_name = name 

    def parse_service_data(self, data):
        """Parse service data."""

    def parse_manufacturer_data(self, data):
        """Parse manufacturer data."""

    def parse_service_class_data(self, data):
        """Parse service class data."""

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
        
        onBytes = bytes([231, 240 + pin, 1])
        offBytes = bytes([231, 240 + pin, 0])

        self.hass.data[DOMAIN][CUTECARE_LOCK].acquire()
        self.hass.data[DOMAIN][CUTECARE_STATE] = False
        try:
            retries = 6
            while retries > 0:
                retries -= 1

                try:
                    device = Peripheral(self.mac)
                    device.writeCharacteristic( 7, onBytes if state else offBytes, False)
                    device.writeCharacteristic( 7, onBytes if state else offBytes, False)
                    device.disconnect()
                    _LOGGER.info("GPIO of JDY08 has been set")
                    break

                except BTLEException as e:
                    _LOGGER.error("Unable set GPIO of JDY08: %s" % e)
                    sleep(0.5)
        finally:
            self.hass.data[DOMAIN][CUTECARE_STATE] = True
            self.hass.data[DOMAIN][CUTECARE_LOCK].release()


class CC41ADevice(CuteCareDevice):
    def __init__(self, hass, mac):
        self._major = 0
        self._minor = 0
        CuteCareDevice.__init__(self, hass, mac)

    @property
    def should_poll(self):
        return False

    @property
    def value(self):
        return self._major

    @property
    def battery(self):
        return self._minor

    def parse_manufacturer_data(self, data):
        """Parse manufacturer data."""

        segments = list(map(''.join, zip(*[iter(data)]*4)))
        if len(segments) > 11:
            self._major = int(segments[10], 16)
            self._minor = int(segments[11], 16)

        self.schedule_update_ha_state(True)


class JDY10Device(CuteCareDevice):
    def __init__(self, hass, mac):
        self._major = 0
        self._minor = 0
        CuteCareDevice.__init__(self, hass, mac)

    @property
    def should_poll(self):
        return False

    @property
    def valueHigh(self):
        return self._major

    @property
    def valueLow(self):
        return self._minor

    def parse_service_class_data(self, data):
        segments = list(map(''.join, zip(*[iter(data)]*2)))
        if len(segments) > 1:
            value = (int(segments[1], 16) << 8) + int(segments[0], 16)
            self._major = value >> 6
            self._minor = value & 0x003F

        self.schedule_update_ha_state(True)
