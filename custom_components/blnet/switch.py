"""
Connect to a BL-NET via it's web interface and read and write data

Switch to control digital outputs
"""
import logging

from homeassistant.const import (
    STATE_UNKNOWN)
from homeassistant.components.switch import SwitchDevice

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'blnet'

MODE = 'mode'
FRIENDLY_NAME = 'friendly_name'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the BLNET component"""

    if discovery_info is None:
        _LOGGER.error("No BL-Net communication configured")
        return False

    switch_id = discovery_info['id']
    blnet_id = discovery_info['name']
    comm = hass.data['DATA_{}'.format(DOMAIN)]

    add_devices([BLNETSwitch(switch_id, blnet_id, comm),
                 BLNETModeSwitch(switch_id, blnet_id, comm)], True)
    return True


class BLNETSwitch(SwitchDevice):
    """
    Representation of a switch that toggles a digital output of the UVR1611.
    """

    def __init__(self, switch_id, blnet_id, comm):
        """Initialize the switch."""
        self._blnet_id = blnet_id
        self._id = switch_id
        self.communication = comm
        self._name = blnet_id
        self._friendly_name = blnet_id
        self._state = STATE_UNKNOWN
        self._assumed_state = True
        self._icon = None
        self._mode = STATE_UNKNOWN
        self._last_updated = None

    def update(self):
        """Get the latest data from communication device """
        # check if new data has arrived
        last_blnet_update = self.communication.last_updated()

        if last_blnet_update == self._last_updated:
            return

        sensor_data = self.communication.data.get(self._blnet_id)

        if sensor_data is None:
            return

        self._friendly_name = sensor_data.get('friendly_name')
        if sensor_data.get('value') == 1:
            self._state = 'on'
        # Nonautomated switch, toggled off => switch off
        else:
            self._state = 'off'
        self._icon = sensor_data.get('icon')
        self._mode = sensor_data.get('mode')

        self._last_updated = last_blnet_update
        self._assumed_state = False

    @property
    def name(self):
        """Return the name of the switch."""
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
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {}

        attrs[MODE] = self._mode
        attrs[FRIENDLY_NAME] = self._friendly_name
        return attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.communication.turn_on(self._id)
        self._state = 'on'
        self._assumed_state = True

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.communication.turn_off(self._id)
        self._state = 'off'
        self._assumed_state = True

    @property
    def assumed_state(self)->bool:
        return self._assumed_state

class BLNETModeSwitch(SwitchDevice):
    """
    Representation of a switch that toggles the operation mode
    of a digital output of the UVR1611. On means automated
    """

    def __init__(self, switch_id, blnet_id, comm):
        """Initialize the switch."""
        self._blnet_id = blnet_id
        self._id = switch_id
        self.communication = comm
        self._name = '{} automated'.format(blnet_id)
        self._friendly_name = blnet_id
        self._state = STATE_UNKNOWN
        self._activation_state = self._state
        self._assumed_state = True
        self._icon = None
        self._last_updated = None

    def update(self):
        """Get the latest data from communication device """
        # check if new data has arrived
        last_blnet_update = self.communication.last_updated()

        if last_blnet_update == self._last_updated:
            return

        sensor_data = self.communication.data.get(self._blnet_id)

        if sensor_data is None:
            return

        self._friendly_name = "{} automated".format(
            sensor_data.get('friendly_name'))
        if sensor_data.get('mode') == 'HAND':
            self._state = 'off'
            self._icon = 'mdi:gesture-tap'
        else:
            self._state = 'on'
            self._icon = 'mdi:settings'
        
        self._activation_state = sensor_data.get('value')

        self._last_updated = last_blnet_update
        self._assumed_state = False

    @property
    def name(self):
        """Return the name of the switch."""
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
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {}
        attrs[FRIENDLY_NAME] = self._friendly_name
        return attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.communication.turn_auto(self._id)
        self._state = 'on'
        self._assumed_state = True

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._activation_state == 1:
            self.communication.turn_on(self._id)
        else:
            self.communication.turn_off(self._id)
        self._state = 'off'
        self._assumed_state = True

    @property
    def assumed_state(self)->bool:
        return self._assumed_state
