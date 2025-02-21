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
    blnet_id = discovery_info['blnet_id']
    name = discovery_info['name']
    friendly_name = discovery_info['friendly_name']
    _LOGGER.debug(f"Discovery info: {discovery_info}")
    comm = hass.data['DATA_{}'.format(DOMAIN)]

    add_devices([BLNETComponent(hass, sensor_id, name, blnet_id, friendly_name, comm)], True)
    return True


class BLNETComponent(Entity):
    """Implementation of a BL-NET - UVR1611 sensor and switch component."""

    def __init__(self, hass, sensor_id, name, blnet_id, friendly_name, communication):
        """Initialize the BL-NET sensor."""
        self._identifier = blnet_id
        self.communication = communication
        self._name = name
        self._friendly_name = friendly_name
        self._state = None
        self._unit_of_measurement = None
        self._icon = None

    @property
    def friendly_name(self):
        """Return the friendly name of the sensor."""
        return self._friendly_name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"blnet_sensor_{self._identifier}"

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
        sensor_data = self.communication.data.get(self._identifier)
        
        if sensor_data is None:
            _LOGGER.warning(f"No data found for sensor {self._identifier}")
            return

        _LOGGER.debug(f"Found sensor data: {sensor_data}")
        # we simply set the identifier using the data from the sensor
        # self._identifier = sensor_data.get('friendly_name')
        # self._name = sensor_data.get('friendly_name')

        self._friendly_name = sensor_data.get('friendly_name')
        self._state = sensor_data.get('value')
        self._unit_of_measurement = sensor_data.get('unit_of_measurement')
        self._icon = sensor_data.get('icon')
