"""
Connect to a BL-NET via it's web interface and read and write data
"""
import logging
from datetime import datetime, timedelta

import voluptuous as vol
from homeassistant.const import (
    CONF_RESOURCE, CONF_PASSWORD, CONF_SCAN_INTERVAL, UnitOfTemperature,
)
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pyblnet==0.9.3']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'blnet'

# Configuration constants
CONF_WEB_PORT = 'web_port'
CONF_TA_PORT = 'ta_port'
CONF_USE_WEB = 'use_web'
CONF_USE_TA = 'use_ta'
CONF_NODE = 'can_node'

# Defaults
DEFAULT_WEB_PORT = 80
DEFAULT_TA_PORT = 40000
DEFAULT_SCAN_INTERVAL = 360

# Unit and icon mappings
UNIT_MAPPINGS = {
    'analog': UnitOfTemperature.CELSIUS,
    'speed': 'rpm',
    'power': 'kW',
    'energy': 'kWh'
}

ICON_MAPPINGS = {
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
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
        vol.Optional(CONF_WEB_PORT, default=DEFAULT_WEB_PORT): cv.positive_int,
        vol.Optional(CONF_TA_PORT, default=DEFAULT_TA_PORT): cv.positive_int,
        vol.Optional(CONF_USE_WEB, default=True): cv.boolean,
        vol.Optional(CONF_USE_TA, default=False): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the BLNET component."""
    from pyblnet import BLNET

    # Extract configuration
    conf = config[DOMAIN]
    resource = conf.get(CONF_RESOURCE)
    password = conf.get(CONF_PASSWORD)
    can_node = conf.get(CONF_NODE)
    scan_interval = conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    web_port = conf.get(CONF_WEB_PORT, DEFAULT_WEB_PORT)
    ta_port = conf.get(CONF_TA_PORT, DEFAULT_TA_PORT)
    use_web = conf.get(CONF_USE_WEB, True)
    use_ta = conf.get(CONF_USE_TA, False)

    _LOGGER.debug(
        f"Setting up BLNET with: resource={resource}, web_port={web_port}, "
        f"ta_port={ta_port}, use_web={use_web}, use_ta={use_ta}"
    )

    blnet_connector = BLNETConnector(
        resource=resource,
        password=password,
        web_port=web_port,
        ta_port=ta_port,
        use_web=use_web,
        use_ta=use_ta
    )
    
    try:
        blnet = blnet_connector.connect()
    except (ValueError, AssertionError) as ex:
        _LOGGER.error(f"Could not connect to BLNET at {resource}: {ex}")
        return False

    # Initialize the data handler
    data_handler = BLNETDataHandler(blnet, can_node, hass, conf)
    hass.data[f"DATA_{DOMAIN}"] = data_handler

    # Set up periodic updates
    update_handler = BLNETUpdateHandler(hass, data_handler, scan_interval)
    update_handler.schedule_updates()

    return True


class BLNETConnector:
    """Handles connection to BLNET device."""
    
    def __init__(self, resource, password=None, web_port=DEFAULT_WEB_PORT,
                 ta_port=DEFAULT_TA_PORT, use_web=True, use_ta=False):
        """Initialize the connector with explicit parameters."""
        self.resource = resource
        self.password = password
        self.web_port = web_port
        self.ta_port = ta_port
        self.use_web = use_web
        self.use_ta = use_ta

    def connect(self):
        """Create and return BLNET connection."""
        from pyblnet import BLNET
        return BLNET(
            self.resource,
            password=self.password,
            web_port=self.web_port,
            ta_port=self.ta_port,
            use_web=self.use_web,
            use_ta=self.use_ta
        )

    def get_error_message(self, exception, resource):
        """Generate appropriate error message."""
        if isinstance(exception, ValueError):
            return f"No BL-Net reached at {resource}"
        return f"Configuration invalid: {exception}"


class BLNETDataHandler:
    """Handles data operations for BLNET."""

    def __init__(self, blnet, node, hass, config):
        """Initialize the data handler."""
        self.blnet = blnet
        self.node = node
        self.data = {}
        self._last_updated = None
        self._hass = hass
        self._config = config
        self.sensors = set()

    def last_updated(self):
        """Return the timestamp of the last update."""
        return self._last_updated

    def turn_off(self, switch_id):
        """Turn off a switch."""
        _LOGGER.debug(f"Turning off switch {switch_id}")
        try:
            self.blnet.turn_off(switch_id, self.node)
            return True
        except Exception as ex:
            _LOGGER.error(f"Error turning off switch {switch_id}: {ex}")
            return False

    def turn_on(self, switch_id):
        """Turn on a switch."""
        _LOGGER.debug(f"Turning on switch {switch_id}")
        try:
            self.blnet.turn_on(switch_id, self.node)
            return True
        except Exception as ex:
            _LOGGER.error(f"Error turning on switch {switch_id}: {ex}")
            return False

    def turn_auto(self, switch_id):
        """Set switch to auto mode."""
        _LOGGER.debug(f"Setting switch {switch_id} to auto mode")
        try:
            self.blnet.turn_auto(switch_id, self.node)
            return True
        except Exception as ex:
            _LOGGER.error(f"Error setting switch {switch_id} to auto: {ex}")
            return False

    def update(self):
        """Update all data and handle sensor discovery."""
        self._last_updated = datetime.now()
        data = self._fetch_data()
        self._update_sensor_data(data)
        self._discover_new_devices(data)
        return data

    def _fetch_data(self):
        """Fetch raw data from BLNET device."""
        return self.blnet.fetch(self.node)

    def _update_sensor_data(self, data):
        """Update data for existing sensors."""
        _LOGGER.info("Updating sensor data...")
        self._update_domain_sensors(data)
        self._update_digital_sensors(data)

    def _update_domain_sensors(self, data):
        """Update sensors for all domains."""
        for domain in ['analog', 'speed', 'power', 'energy']:
            for key, sensor in data.get(domain, {}).items():
                self._update_single_sensor(domain, key, sensor)

    def _update_single_sensor(self, domain, key, sensor):
        """Update a single sensor's attributes."""
        entity_id = f'{DOMAIN} {domain} {key}'
        self.data[entity_id] = {
            'value': sensor.get('value'),
            'unit_of_measurement': sensor.get('unit_of_measurement', UNIT_MAPPINGS[domain]),
            'friendly_name': sensor.get('name'),
            'icon': ICON_MAPPINGS[domain]
        }

    def _update_digital_sensors(self, data):
        """Update digital sensors."""
        for key, sensor in data.get('digital', {}).items():
            entity_id = f'{DOMAIN} digital {key}'
            self.data[entity_id] = {
                'friendly_name': sensor.get('name'),
                'mode': sensor.get('mode'),
                'value': sensor.get('value')
            }

    def _discover_new_devices(self, data):
        """Handle discovery of new devices."""
        added_count = self._discover_sensors(data)
        added_count += self._discover_digital_devices(data)
        if added_count > 0:
            _LOGGER.info(f"Added {added_count} new devices")

    def _discover_sensors(self, data):
        """Discover and add new sensors."""
        added_count = 0
        for domain in ['analog', 'speed', 'power', 'energy']:
            for sensor_id in data[domain]:
                if self._add_single_sensor(domain, sensor_id, data):
                    added_count += 1
        return added_count

    def _add_single_sensor(self, domain, sensor_id, data):
        """Add a single new sensor."""
        name = data[domain][sensor_id].get('name')
        blnet_id = '{} {} {}'.format(DOMAIN, domain, sensor_id)
        if name in self.sensors:
            return False

        self.sensors.add(name)
        _LOGGER.info(f"Discovered {domain} sensor {sensor_id} in use, adding")

        disc_info = {
            'name': name,
            'domain': domain,
            'id': sensor_id,
            'friendly_name': name,
            'blnet_id': blnet_id
        }
        _LOGGER.debug(f"Sensor data for {domain}[{sensor_id}]: {data[domain][sensor_id]} - Disc info: {disc_info}")
        load_platform(self._hass, 'sensor', DOMAIN, disc_info, self._config)
        return True

    def _discover_digital_devices(self, data):
        """Discover and add new digital devices."""
        added_count = 0
        for sensor_id in data['digital']:
            if self._add_digital_device(sensor_id, data):
                added_count += 1
        return added_count

    def _add_digital_device(self, sensor_id, data):
        """Add a single new digital device."""
        name = data['digital'][sensor_id].get('name')
        blnet_id = '{} digital {}'.format(DOMAIN, sensor_id)
        if name in self.sensors:
            return False

        self.sensors.add(name)
        _LOGGER.info(f"Discovered digital sensor {sensor_id} in use, adding")

        disc_info = {
            'name': name,
            'domain': 'digital',
            'id': sensor_id,
            'friendly_name': name,
            'blnet_id': blnet_id
        }
        component = 'switch' if self._config[CONF_USE_WEB] else 'sensor'
        load_platform(self._hass, component, DOMAIN, disc_info, self._config)
        return True


class BLNETUpdateHandler:
    """Handles periodic updates for BLNET."""

    def __init__(self, hass, data_handler, scan_interval):
        self.hass = hass
        self.data_handler = data_handler
        self.scan_interval = scan_interval

    def schedule_updates(self):
        """Schedule periodic updates."""
        def fetch_data(*_):
            return self.data_handler.update()

        # Initial update
        fetch_data()
        
        # Schedule periodic updates
        async_track_time_interval(
            self.hass,
            fetch_data,
            timedelta(seconds=self.scan_interval)
        )
