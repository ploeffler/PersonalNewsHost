"""Configuration must fail before any RSS request or rendering side effect."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import generate
from scripts.validate_config import validate_config

ROOT = Path(__file__).resolve().parents[1]


class ConfigValidationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'config.example.json').read_text())

    def test_repository_configs_are_valid(self):
        for name in ('config.json', 'config.example.json'):
            validate_config(json.loads((ROOT / name).read_text()))

    def test_invalid_core_values(self):
        for key, value in [('feeds', ['file:///etc/passwd']), ('max_items', 0),
                           ('max_items', True), ('title', ''), ('max_items', 1.5)]:
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_config(config)

    def test_bad_timezone_and_budget(self):
        self.config['automation']['timezone'] = 'Not/AZone'
        with self.assertRaises(ValueError): validate_config(self.config)
        self.config['automation']['timezone'] = 'UTC'
        self.config['advanced_services']['max_per_month_eur'] = -1
        with self.assertRaises(ValueError): validate_config(self.config)

    def test_non_finite_numbers_even_in_extensions(self):
        self.config['extension'] = {'amount': float('nan')}
        with self.assertRaises(ValueError): validate_config(self.config)

    def test_error_does_not_echo_secret(self):
        self.config['max_items'] = 'private-token-should-not-leak'
        with self.assertRaises(ValueError) as error: validate_config(self.config)
        self.assertNotIn('private-token', str(error.exception))

    def test_invalid_config_stops_before_feed_fetch(self):
        self.config['max_items'] = -1
        with patch.object(generate, 'CONFIG', self.config), patch.object(generate, 'items_from_feed') as fetch:
            with self.assertRaises(ValueError): generate.main()
            fetch.assert_not_called()


if __name__ == '__main__': unittest.main()
