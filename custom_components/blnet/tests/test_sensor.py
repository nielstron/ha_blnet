"""Tests for the BLNET sensor component."""
import unittest
from unittest.mock import Mock
from custom_components.blnet.sensor import BLNETComponent

class TestBLNETComponent(unittest.TestCase):
    """Test the BLNETComponent class."""

    def setUp(self):
        """Set up test variables."""
        self.hass = Mock()
        self.communication = Mock()

    def test_init_with_numeric_sensor_id(self):
        """Test initialization with numeric sensor_id."""
        sensor = BLNETComponent(
            hass=self.hass,
            sensor_id=1,
            name="test_sensor",
            friendly_name="Test Sensor",
            communication=self.communication
        )
        self.assertEqual(sensor._identifier, "Test Sensor_1")
        self.assertEqual(sensor._friendly_name, "Test Sensor")

    def test_init_with_string_sensor_id(self):
        """Test initialization with string sensor_id."""
        sensor = BLNETComponent(
            hass=self.hass,
            sensor_id="A1",
            name="test_sensor",
            friendly_name="Test Sensor",
            communication=self.communication
        )
        self.assertEqual(sensor._identifier, "Test Sensor_A1")
        self.assertEqual(sensor._friendly_name, "Test Sensor")

if __name__ == '__main__':
    unittest.main() 