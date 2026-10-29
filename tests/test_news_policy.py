import unittest
from unittest.mock import patch
from scripts.news_policy import allowed, category
from scripts import generate


class NewsPolicyTests(unittest.TestCase):
    def setUp(self):
        self.entry = ('New technology', 'Description', 'https://news.example/story', [])
        self.feed = 'https://news.example/rss'

    def test_default_and_category_filter(self):
        self.assertEqual(category(self.entry, self.feed, {}), 'general')
        config = {'feed_categories': {self.feed: 'tech'}, 'category_filter': ['tech']}
        self.assertTrue(allowed(self.entry, self.feed, config))
        self.assertFalse(allowed(self.entry, 'https://other.example/rss', config))

    def test_domain_boundary_and_feed_block(self):
        for url, blocked in [('https://bad.example/a', True), ('https://sub.bad.example/a', True),
                             ('https://notbad.example/a', False)]:
            entry = (self.entry[0], self.entry[1], url, [])
            self.assertEqual(not allowed(entry, self.feed, {'source_policy': {'blocked_domains': ['bad.example']}}), blocked)
        self.assertFalse(allowed(self.entry, self.feed, {'source_policy': {'blocked_domains': ['news.example']}}))

    def test_keyword_and_block_override_weight(self):
        config = {'source_policy': {'excluded_keywords': ['TECHNOLOGY'], 'weights': {'news.example': 100}}}
        self.assertFalse(allowed(self.entry, self.feed, config))

    def test_weights_change_order_but_defaults_keep_recency(self):
        other = ('Other report', '', 'https://other.example/story', [])
        with patch.object(generate, 'FEED_DATES', {self.entry[2]: 1, other[2]: 2}), \
             patch.object(generate, 'CONFIG', {'source_policy': {'weights': {'news.example': 2}}}):
            self.assertEqual(generate.select_balanced_groups([[other], [self.entry]], 1), [[self.entry]])
        with patch.object(generate, 'FEED_DATES', {self.entry[2]: 1, other[2]: 2}), patch.object(generate, 'CONFIG', {}):
            self.assertEqual(generate.select_balanced_groups([[self.entry], [other]], 1), [[other]])
