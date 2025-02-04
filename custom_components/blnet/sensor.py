"""
Connect to a BL-NET via it's web interface and read and write data
"""
import logging

from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'blnet'
FRIENDLY_NAME = 'friendly_name'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the BLNET component"""

    if discovery_info is None:
        _LOGGER.error("No BL-Net communication configured")
        return False

    sensor_id = discovery_info['id']
    blnet_id = discovery_info['name']
    _LOGGER.debug(f"Discovery info: {discovery_info}")
    comm = hass.data['DATA_{}'.format(DOMAIN)]

    add_devices([BLNETComponent(hass, sensor_id, blnet_id, comm)], True)
    return True


class BLNETComponent(Entity):
    """Implementation of a BL-NET - UVR1611 sensor and switch component."""

    def __init__(self, hass, sensor_id, name, communication):
        """Initialize the BL-NET sensor."""
        self._identifier = name
        self.communication = communication
        self._name = name
        self._friendly_name = name
        self._state = None
        self._unit_of_measurement = None
        self._icon = None

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"blnet_sensor_{self._identifier}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the state of the device."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the state of the device."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {}

        attrs[FRIENDLY_NAME] = self._friendly_name
        return attrs

    def update(self):
        """Get the latest data from communication device """
        _LOGGER.debug(f"Trying to update sensor {self._identifier}")
        _LOGGER.debug(f"Available data: {self.communication.data}")
        
        sensor_data = self.communication.data.get(self._identifier)

        # we simply set the identifier using the data from the sensor
        self._identifier = self.communication.data.get('friendly_name')
        self._name = self.communication.data.get('friendly_name')
        
        if sensor_data is None:
            _LOGGER.warning(f"No data found for sensor {self._identifier}")
            return

        _LOGGER.debug(f"Found sensor data: {sensor_data}")
        self._friendly_name = sensor_data.get('friendly_name')
        self._state = sensor_data.get('value')
        self._unit_of_measurement = sensor_data.get('unit_of_measurement')
        self._icon = sensor_data.get('icon')
