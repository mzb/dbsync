import unittest
from nose.tools import *

import dbsync


class SQLMigrationParsing(unittest.TestCase):

    def test_parses_simple_migration_into_up_and_down_changes(self):
        migration = dbsync.parse_sql_migration('''
            -- @UP
            CREATE TABLE users
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': 'DROP TABLE users'}, migration)

    def test_parses_into_empty_up_or_down_changes_when_annotation_not_found(self):
        migration = dbsync.parse_sql_migration('''
            -- @UP
            CREATE TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': None}, migration, 'No DOWN change')

        migration = dbsync.parse_sql_migration('''
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': None, 'down': 'DROP TABLE users'}, migration, 'No UP change')

    def test_is_not_confused_by_annotations_inside_sql(self):
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
        
