"""Deterministic category mapping and explicit source selection rules."""
from urllib.parse import urlsplit


def domain(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.')


def matches(host, rule):
    return host == rule or host.endswith('.' + rule)


def category(entry, feed, config):
    return config.get('feed_categories', {}).get(feed, 'general')


def allowed(entry, feed, config):
    policy = config.get('source_policy', {})
    hosts = (domain(entry[2]), domain(feed))
    if any(matches(host, rule.lower().removeprefix('www.'))
           for rule in policy.get('blocked_domains', []) for host in hosts):
        return False
    text = (entry[0] + ' ' + entry[1]).casefold()
    if any(term.casefold() in text for term in policy.get('excluded_keywords', [])):
        return False
    categories = config.get('category_filter', [])
    return not categories or category(entry, feed, config) in categories


def source_weight(entry, config):
    host = domain(entry[2])
    candidates = [(len(rule), value) for rule, value in
                  config.get('source_policy', {}).get('weights', {}).items()
                  if matches(host, rule.lower().removeprefix('www.'))]
    return max(candidates, default=(0, 1))[1]
