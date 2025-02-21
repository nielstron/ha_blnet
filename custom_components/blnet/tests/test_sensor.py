"""Tests for the BLNET sensor component."""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from custom_components.blnet.sensor import BLNETComponent
from custom_components.blnet import BLNETDataHandler, BLNETConnector

class TestBLNETComponent(unittest.TestCase):
    """Test the BLNETComponent class."""

    def setUp(self):
        """Set up test variables."""
        self.hass = Mock()
        self.communication = Mock()
        self.communication.data = {}
        self.communication.last_updated = Mock(return_value=datetime.now())

    def test_init_with_numeric_sensor_id(self):
        """Test initialization with numeric sensor_id."""
        sensor = BLNETComponent(
            hass=self.hass,
            sensor_id=1,
            name="test_sensor",
            blnet_id="test_blnet_1",
            friendly_name="Test Sensor",
            communication=self.communication
        )
        self.assertEqual(sensor._identifier, "test_blnet_1")
        self.assertEqual(sensor._friendly_name, "Test Sensor")
        self.assertEqual(sensor._name, "test_sensor")
        self.assertEqual(sensor.name, "test_sensor")

    def test_init_with_string_sensor_id(self):
        """Test initialization with string sensor_id."""
        sensor = BLNETComponent(
            hass=self.hass,
            sensor_id="A1",
            name="test_sensor",
            blnet_id="test_blnet_A1",
            friendly_name="Test Sensor",
            communication=self.communication
        )
        self.assertEqual(sensor._identifier, "test_blnet_A1")
        self.assertEqual(sensor._friendly_name, "Test Sensor")


class TestBLNETDataHandler(unittest.TestCase):
    """Test the BLNETDataHandler class."""

    def setUp(self):
        """Set up test variables."""
        self.hass = Mock()
        self.blnet = Mock()
        self.config = {
            'resource': 'http://example.com',
            'password': 'test',
            'web_port': 80,
            'ta_port': 40000,
            'use_web': True,
            'use_ta': False
        }
        self.node = 1

    def test_init(self):
        """Test initialization of data handler."""
        handler = BLNETDataHandler(self.blnet, self.node, self.hass, self.config)
        self.assertEqual(handler.blnet, self.blnet)
        self.assertEqual(handler.node, self.node)
        self.assertEqual(handler._hass, self.hass)
        self.assertEqual(handler._config, self.config)
        self.assertEqual(handler.data, {})
        self.assertIsNone(handler._last_updated)

    def test_last_updated(self):
        """Test last_updated method."""
        handler = BLNETDataHandler(self.blnet, self.node, self.hass, self.config)
        self.assertIsNone(handler.last_updated())
        handler._last_updated = datetime.now()
        self.assertIsNotNone(handler.last_updated())

    def test_turn_on_off(self):
        """Test turn_on and turn_off methods."""
        handler = BLNETDataHandler(self.blnet, self.node, self.hass, self.config)
        
        # Test turn_on
        handler.turn_on(1)
        self.blnet.turn_on.assert_called_once_with(1, self.node)
        
        # Test turn_off
        handler.turn_off(1)
        self.blnet.turn_off.assert_called_once_with(1, self.node)
        
        # Test turn_auto
        handler.turn_auto(1)
        self.blnet.turn_auto.assert_called_once_with(1, self.node)


class TestBLNETConnector(unittest.TestCase):
    """Test the BLNETConnector class."""

    def test_init(self):
        """Test initialization of connector."""
        connector = BLNETConnector(
            resource='http://example.com',
            password='test',
            web_port=80,
            ta_port=40000,
            use_web=True,
            use_ta=False
        )
        self.assertEqual(connector.resource, 'http://example.com')
        self.assertEqual(connector.password, 'test')
        self.assertEqual(connector.web_port, 80)
        self.assertEqual(connector.ta_port, 40000)
        self.assertTrue(connector.use_web)
        self.assertFalse(connector.use_ta)

    @patch('pyblnet.BLNET')
    def test_connect(self, mock_blnet):
        """Test connect method."""
        connector = BLNETConnector(
            resource='http://example.com',
            password='test'
        )
        connector.connect()
        mock_blnet.assert_called_once_with(
            'http://example.com',
            password='test',
            web_port=80,
            ta_port=40000,
            use_web=True,
            use_ta=False
        )


if __name__ == '__main__':
    unittest.main() 
