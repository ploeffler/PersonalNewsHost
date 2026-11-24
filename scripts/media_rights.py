"""Bildrechte und Bildnachweis pro Meldung (T062).

Jedes Bild einer Sendung bekommt einen Nachweis in ``docs/media-credits.json``
(``image_origin``, ``license_status``, ``license``, ``holder``, ``basis``).

* ``licensed``: nachweisbar passende Lizenz. Das sind Bilder aus Quellen, die der
  Betreiber unter ``media.licensed_sources`` mit Lizenz freigegeben hat, sowie
  Bilder aus Wikimedia Commons mit Public-Domain-/CC0-Lizenz (geprüft über die
  Commons-Metadaten) und selbst erzeugte Grafiken.
* ``unverified``: Veröffentlichungsbild einer Quelle ohne Freigabe. Standard
  (``media.license_policy: "strict"``): nicht verwenden, es folgt Commons oder die
  selbst erzeugte Nachrichtentafel. ``"record_only"`` verwendet es weiter und
  vermerkt nur den fehlenden Nachweis.
"""
import re
from urllib.parse import urlsplit

STRICT, RECORD_ONLY = 'strict', 'record_only'
LICENSED, UNVERIFIED, REJECTED = 'licensed', 'unverified', 'rejected_unverified'
ORIGINS = ('publisher_image', 'commons', 'generated_graphic')
REQUIRED = ('source', 'image_origin', 'license_status')


def policy(config):
    value = ((config.get('media') or {}).get('license_policy')) if isinstance(config, dict) else None
    return RECORD_ONLY if value == RECORD_ONLY else STRICT


def _host(url):
    host = (urlsplit(str(url)).hostname or '').lower()
    return host[4:] if host.startswith('www.') else host


def licensed_source(config, *urls):
    """Operator-approved source entry covering one of the URLs, else None."""
    entries = (config.get('media') or {}).get('licensed_sources') or []
    hosts = {_host(url) for url in urls if url}
    for entry in entries:
        host = _host('//' + str(entry.get('host', '')).lower()) if isinstance(entry, dict) else ''
        if host and any(h == host or h.endswith('.' + host) for h in hosts):
            return entry
    return None


def publisher_credit(source_url, image_url, config):
    entry = licensed_source(config, image_url, source_url)
    credit = {'source': source_url, 'image_origin': 'publisher_image', 'image_url': str(image_url or '')}
    if entry and str(entry.get('license', '')).strip():
        credit.update(license_status=LICENSED, license=str(entry['license']).strip()[:80],
                      holder=str(entry.get('holder') or _host(source_url))[:120],
                      basis='Freigabe des Betreibers (media.licensed_sources)')
    else:
        credit.update(license_status=UNVERIFIED, license='', holder=_host(source_url),
                      basis='Keine nachweisbare Lizenz')
    return credit


def commons_credit(source_page, title, license_name, artist=''):
    return {'source': source_page, 'image_origin': 'commons', 'license_status': LICENSED,
            'license': str(license_name)[:80], 'holder': re.sub(r'<[^>]+>', '', str(artist or 'Wikimedia Commons'))[:120],
            'title': title, 'basis': 'Wikimedia Commons, Lizenz aus den Metadaten geprüft',
            'note': 'Illustrationsbild, nicht zwingend Aufnahme des Ereignisses'}


def generated_credit(source_url):
    return {'source': source_url, 'image_origin': 'generated_graphic', 'license_status': LICENSED,
            'license': 'eigene Grafik', 'holder': 'PersonalNewsHost', 'basis': 'Automatisch erzeugte Nachrichtentafel'}


def usable(credit, config):
    return policy(config) == RECORD_ONLY or credit.get('license_status') == LICENSED


def reject(credit):
    return {**credit, 'license_status': REJECTED, 'rejected': True}


def credit_text(credit):
    """Short credit line for article pages; empty if there is nothing to show."""
    if not credit or credit.get('license_status') not in (LICENSED, UNVERIFIED):
        return ''
    origin = credit.get('image_origin')
    holder, lic = credit.get('holder') or '', credit.get('license') or ''
    if origin == 'generated_graphic':
        return 'Bild: automatisch erzeugte Grafik'
    if origin == 'commons':
        return f"Illustrationsbild: {holder}{', ' + lic if lic else ''} (Wikimedia Commons)"
    base = f'Bild: {holder}' + (f', {lic}' if lic else '')
    return base + ('' if credit.get('license_status') == LICENSED else ' (Lizenz nicht nachgewiesen)')


def outro_line(credits, limit=52):
    holders = []
    for credit in credits:
        if credit and credit.get('license_status') == LICENSED and credit.get('image_origin') != 'generated_graphic':
            name = credit.get('holder')
            if name and name not in holders:
                holders.append(name)
    if not holders:
        return 'Bilder: eigene Grafiken'
    line = 'Bilder: ' + ', '.join(holders)
    return line if len(line) <= limit else line[:limit - 1].rstrip(', ') + '…'


def validate_credits(credits):
    """Problems of a media-credits list: every image needs a complete record."""
    errors = []
    for index, credit in enumerate(credits):
        if not isinstance(credit, dict):
            errors.append(f'{index}: kein Objekt')
            continue
        errors += [f'{index}: {key} fehlt' for key in REQUIRED if not credit.get(key)]
        if credit.get('image_origin') and credit['image_origin'] not in ORIGINS:
            errors.append(f"{index}: unbekannte Herkunft {credit['image_origin']}")
        if credit.get('license_status') == LICENSED and not credit.get('license'):
            errors.append(f'{index}: Lizenz fehlt')
    return errors
