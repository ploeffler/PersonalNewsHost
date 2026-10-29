import json
from pathlib import Path
import socket
import unittest
from scripts import generate
from scripts.build_example_show import FIXTURE, configuration, fixture_inputs
from scripts.validate_config import validate_config
from unittest.mock import patch


class ExampleShowTests(unittest.TestCase):
    def test_fixture_and_configuration(self):
        fixture=json.loads(FIXTURE.read_text())
        self.assertEqual(fixture['newsroom']['name'],'Allgemein')
        self.assertEqual(len(fixture['stories']),3)
        validate_config(configuration(fixture))
        self.assertFalse(configuration(fixture)['automation']['enabled'])

    def test_fixture_restores_sources_and_blocks_network(self):
        fixture=json.loads(FIXTURE.read_text());old=generate.items_from_feed;dns=socket.getaddrinfo
        with self.assertRaisesRegex(RuntimeError,'test error'):
            with fixture_inputs(fixture):
                self.assertEqual(len(generate.items_from_feed('unused')),3)
                with self.assertRaises(OSError):socket.getaddrinfo('example.org',443)
                raise RuntimeError('test error')
        self.assertIs(generate.items_from_feed,old)
        self.assertIs(socket.getaddrinfo,dns)

    def test_example_strapline_does_not_claim_live(self):
        fixture=json.loads(FIXTURE.read_text())
        with patch.object(generate,'run') as run:
            with fixture_inputs(fixture):
                generate.run(['ffmpeg',"text='KI  /  NEWS  /  LIVE'"])
            args=run.call_args.args[0]
            self.assertIn('BEISPIEL',args[1])
            self.assertNotIn('LIVE',args[1])

    def test_workflow_only_updates_development_demo(self):
        text=(Path(__file__).resolve().parents[1]/'.github/workflows/example-newsshow.yml').read_text()
        self.assertIn("github.ref == 'refs/heads/Full-featured-Newsoutlet'",text)
        self.assertNotIn('schedule:',text)
        self.assertIn('git push origin HEAD:Full-featured-Newsoutlet',text)
        self.assertNotIn('HEAD:main',text)
        self.assertNotIn('secrets.',text)
