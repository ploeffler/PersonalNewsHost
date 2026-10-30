"""Bounded public HTTP reads for feed/operator research; no private-network access."""
import http.client
import ipaddress
import socket
import urllib.parse
import urllib.request

MAX_FEED_BYTES = 1_000_000


def validate_feed_url(url, resolve=True):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in {'http', 'https'} or not p.hostname or p.username or p.password or p.port not in {None, 80, 443}:
        raise ValueError('Feed must be a public HTTP(S) URL without credentials')
    if any(k.casefold() in {'token', 'api_key', 'apikey', 'password', 'secret', 'access_token'} for k, _ in urllib.parse.parse_qsl(p.query)):
        raise ValueError('Feed URL must not include secret parameters')
    if p.hostname.lower() == 'localhost' or p.hostname.lower().endswith(('.localhost', '.local')):
        raise ValueError('Private hostname is not allowed')
    try:
        literal = ipaddress.ip_address(p.hostname)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise ValueError('Private/reserved literal address is not allowed')
    if resolve:
        addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('Private/reserved feed addresses are not allowed')
    return url


def checked_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Connect to the checked numeric address; never re-resolve via urllib/proxy."""
    host, port = address
    records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not records or any(not ipaddress.ip_address(row[4][0]).is_global for row in records):
        raise ValueError('Feed connection resolved to a private/reserved address')
    for family, kind, protocol, _, target in records:
        connection = socket.socket(family, kind, protocol)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                connection.settimeout(timeout)
            if source_address:
                connection.bind(source_address)
            connection.connect(target)
            return connection
        except OSError:
            connection.close()
    raise OSError('No public feed address could be reached')


class PublicHTTPConnection(http.client.HTTPConnection):
    def connect(self):
        self._create_connection = checked_connection
        super().connect()


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        self._create_connection = checked_connection
        super().connect()  # Keeps original hostname for TLS verification/SNI.


class PublicHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(PublicHTTPConnection, request)


class PublicHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(PublicHTTPSConnection, request, context=self._context)


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_feed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_public(url):
    validate_feed_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'PersonalNewsHost promo'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({}), PublicHTTPHandler(), PublicHTTPSHandler(), PublicRedirects()).open(request, timeout=20) as response:
        data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise ValueError('Feed exceeds 1 MB limit')
    return data
