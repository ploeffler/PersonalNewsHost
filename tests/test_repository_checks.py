from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import check_repository as check


class RepositoryCheckTests(unittest.TestCase):
    def test_secret_scan_detects_without_exposing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'test.txt';p.write_text('ghp_'+'A'*35)
            with patch.object(check,'ROOT',root):
                errors=check.secrets([p])
            self.assertEqual(len(errors),1)
            self.assertNotIn('A'*35,errors[0])

    def test_missing_links_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'doc.md';p.write_text('[missing](not-here.md) [web](https://example.org)')
            with patch.object(check,'ROOT',root):self.assertEqual(len(check.links([p])),1)

    def test_network_guard_denies_tcp_udp_and_dns_and_restores(self):
        import socket
        original = socket.socket.connect
        with check.offline_network():
            with socket.socket() as client:
                with self.assertRaisesRegex(OSError, 'Network disabled'):
                    client.connect(('127.0.0.1', 9))
            with socket.socket(type=socket.SOCK_DGRAM) as client:
                with self.assertRaisesRegex(OSError, 'Network disabled'):
                    client.sendto(b'test', ('127.0.0.1', 9))
            with self.assertRaisesRegex(OSError, 'Network disabled'):
                socket.getaddrinfo('example.invalid', 443)
        self.assertIs(socket.socket.connect, original)

    def test_site_links_assets_fragments_queries_and_root_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'index.html').write_text('<a href="/other.html?q=1#ok">next</a><img src="image%20one.png"><a href="https://example.invalid/missing">remote</a>')
            (root/'other.html').write_text('<h1 id="ok">Found</h1>')
            (root/'image one.png').write_bytes(b'fixture')
            self.assertEqual(check.site_links(root), [])
            (root/'other.html').write_text('<a href="index.html#missing">bad anchor</a><img src="missing.png"><a href="../escape">escape</a>')
            errors = check.site_links(root)
            self.assertEqual(len(errors), 4)  # old inbound anchor plus three bad targets
