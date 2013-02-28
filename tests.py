import unittest
from nose.tools import *

import dbsync


class ExtractChanges(unittest.TestCase):

    def test_extracts_up_and_down_changes_based_on_annotations(self):
        changes = dbsync.extract_changes('''
            -- @UP
            CREATE TABLE users
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': 'DROP TABLE users'}, changes)

    def test_extracts_empty_change_when_annotation_missing(self):
        changes = dbsync.extract_changes('''
            -- @UP
            CREATE TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': None}, changes, 'No DOWN change')

        changes = dbsync.extract_changes('''
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': None, 'down': 'DROP TABLE users'}, changes, 'No UP change')

        assert_equals({'up': None, 'down': None}, dbsync.extract_changes(''), 'Empty')

    def test_is_not_confused_by_annotation_like_literals_in_sql(self):
        changes = dbsync.extract_changes('''
            -- @UP
            INSERT INTO users VALUES (NULL, "-- @DOWN")
            -- @DOWN
            DELETE FROM users
        ''')
        expected = {
                'up': 'INSERT INTO users VALUES (NULL, "-- @DOWN")',
                'down': 'DELETE FROM users'
        }
        assert_equals(expected, changes)

