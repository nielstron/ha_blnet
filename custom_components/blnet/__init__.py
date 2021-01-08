"""
Connect to a BL-NET via it's web interface and read and write data
"""
import logging

import voluptuous as vol
from homeassistant.helpers.discovery import load_platform

from homeassistant.const import (
    CONF_RESOURCE, CONF_PASSWORD, CONF_SCAN_INTERVAL, TEMP_CELSIUS,
)
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from datetime import datetime
import time
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = [
    'pyblnet==0.9.1'
]

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'blnet'

CONF_WEB_PORT = 'web_port'
CONF_TA_PORT = 'ta_port'
CONF_USE_WEB = 'use_web'
CONF_USE_TA = 'use_ta'
CONF_NODE = 'can_node'
# Defaults
DEFAULT_WEB_PORT = 80
DEFAULT_TA_PORT = 40000
# scan every 6 minutes per default
DEFAULT_SCAN_INTERVAL = 360

UNIT = {
    'analog': TEMP_CELSIUS,
    'speed': 'rpm',
    'power': 'kW',
    'energy': 'kWh'
}
ICON = {
    'analog': 'mdi:thermometer',
    'speed': 'mdi:speedometer',
    'power': 'mdi:power-plug',
    'energy': 'mdi:power-plug'

}

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_RESOURCE): cv.url,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NODE): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL,
                     default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
        vol.Optional(CONF_WEB_PORT, default=DEFAULT_WEB_PORT): cv.positive_int,
        vol.Optional(CONF_TA_PORT, default=DEFAULT_TA_PORT): cv.positive_int,
        vol.Optional(CONF_USE_WEB, default=True): cv.boolean,
        vol.Optional(CONF_USE_TA, default=False): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the BLNET component"""

    from pyblnet import BLNET

    config = config[DOMAIN]
    resource = config.get(CONF_RESOURCE)
    password = config.get(CONF_PASSWORD)
    can_node = config.get(CONF_NODE)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    web_port = config.get(CONF_WEB_PORT)
    ta_port = config.get(CONF_TA_PORT)
    use_web = config.get(CONF_USE_WEB)
    use_ta = config.get(CONF_USE_TA)

    # Initialize the BL-NET sensor
    try:
        blnet = BLNET(resource, password=password, web_port=web_port,
                      ta_port=ta_port, use_web=use_web, use_ta=use_ta)
    except (ValueError, AssertionError) as ex:
        if isinstance(ex, ValueError):
            _LOGGER.error("No BL-Net reached at {}".format(resource))
        else:
            _LOGGER.error("Configuration invalid: {}".format(ex))
        return False


    # set the communication entity
    hass.data["DATA_{}".format(DOMAIN)] = BLNETComm(blnet, can_node, hass, config)

    # make sure the communication device gets updated once in a while
    def fetch_data(*_):
        return hass.data["DATA_{}".format(DOMAIN)].update()

    # Get the latest data from REST API and load
    # sensors and switches accordingly
    data = fetch_data()
    # Repeat if data fetching fails at first
    async_track_time_interval(hass,
                              fetch_data,
                              timedelta(seconds=scan_interval))

    # Fetch method takes care of adding dicovered sensors
    return True


class BLNETComm(object):
    """Implementation of a BL-NET - UVR1611 communication component"""

    def __init__(self, blnet, node, hass, config):
        self.blnet = blnet
        self.node = node
        # Map id -> attributes
        self.data = {}
        self._last_updated = None
        self._hass = hass
        self._config = config
        self.sensors = set()

    def turn_on(self, switch_id):
        # only change active node if this is desired
        self.blnet.turn_on(switch_id, self.node)

    def turn_off(self, switch_id):
        # only change active node if this is desired
        self.blnet.turn_off(switch_id, self.node)

    def turn_auto(self, switch_id):
        # only change active node if this is desired
        self.blnet.turn_auto(switch_id, self.node)

    def last_updated(self):
        return self._last_updated

    def update(self):
        """
        Get the latest data from BLNET and update the state.
        Also adds new states on discovery.
        """

        data = self.blnet.fetch(self.node)

        _LOGGER.info("Collecting data...")
        for domain in ['analog', 'speed', 'power', 'energy']:
            # iterate through the list and store the data for every sensor
            for key, sensor in data.get(domain, {}).items():
                attributes = {}
                entity_id = '{} {} {}'.format(DOMAIN, domain, key)
                attributes['value'] = sensor.get('value')

                attributes['unit_of_measurement'] = sensor.get('unit_of_measurement',
                                                               UNIT[domain])
                attributes['friendly_name'] = sensor.get('name')
                attributes['icon'] = ICON[domain]

                self.data[entity_id] = attributes

        # iterate through the list and store data for every output
        for key, sensor in data.get('digital', {}).items():
            attributes = {}
            entity_id = '{} digital {}'.format(DOMAIN, key)

            attributes['friendly_name'] = sensor.get('name')
            attributes['mode'] = sensor.get('mode')
            attributes['value'] = sensor.get('value')

            self.data[entity_id] = attributes
        # save that the data was updated just now
        self._last_updated = datetime.now()

        _LOGGER.info("Checking for new sensors...")
        # Check if there are new sensors that are to be added
        i = 0
        # iterate through the list and create a sensor for every value
        for domain in ['analog', 'speed', 'power', 'energy']:
            for sensor_id in data[domain]:
                name = '{} {} {}'.format(DOMAIN, domain, sensor_id)
                if name in self.sensors:
                    continue
                self.sensors.add(name)
                _LOGGER.info("Discovered {} sensor {} in use, adding".format(domain, sensor_id))
                i += 1
                disc_info = {
                    'name': name,
                    'domain': domain,
                    'id': sensor_id,
                }
                load_platform(self._hass, 'sensor', DOMAIN, disc_info, self._config)

        # iterate through the list and create a switch for direct control over every output
        for sensor_id in data['digital']:
            name = '{} digital {}'.format(DOMAIN, sensor_id)
            if name in self.sensors:
                continue
            self.sensors.add(name)
            _LOGGER.info("Discovered digital sensor {} in use, adding".format(sensor_id))
            i += 1
            disc_info = {
                'name': name,
                'domain': 'digital',
                'id': sensor_id,
            }
            if self._config.get(CONF_USE_WEB):
                component = 'switch'
            else:
                component = 'sensor'
            load_platform(self._hass, component, DOMAIN, disc_info, self._config)
        if i > 0:
            _LOGGER.info("Added overall {} sensors".format(i))

        return data
