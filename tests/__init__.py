import unittest
from nose.tools import *

import dbsync


class ParseSQLMigration(unittest.TestCase):

    def test_up_and_down_annotations(self):
        migration = dbsync.parse_sql_migration('''
            -- @UP
            CREATE TABLE users
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': 'DROP TABLE users'}, migration)

    def test_one_annotation_missing(self):
        migration = dbsync.parse_sql_migration('''
            -- @UP
            CREATE TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': None}, migration, 
                'Missing @DOWN')

        migration = dbsync.parse_sql_migration('''
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': None, 'down': 'DROP TABLE users'}, migration, 
                'Missing @UP')

    def test_no_annotations(self):
        assert_equals({'up': None, 'down': None}, dbsync.parse_sql_migration(''))

    def test_annotation_like_literals_in_sql_statements(self):
        migration = dbsync.parse_sql_migration('''
            -- @UP
            INSERT INTO users VALUES (NULL, "-- @DOWN")
            -- @DOWN
            DELETE FROM users
        ''')
        expected = {
                'up': 'INSERT INTO users VALUES (NULL, "-- @DOWN")',
                'down': 'DELETE FROM users'
        }
        assert_equals(expected, migration)

