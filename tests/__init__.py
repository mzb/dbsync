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


class SelectChangesToRun(unittest.TestCase):

    def test_no_target_version_no_schema_version(self):
        """Selects all up changes"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        expected = [
                (1, 'UP 1'), (2, 'UP 2'), (3, 'UP 3')
        ]
        assert_equals(expected, dbsync.select_changes_to_run(migrations))

    def test_no_target_version_but_preset_schema_version(self):
        """Selects all up changes above schema version"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        expected = [
                (3, 'UP 3')
        ]
        assert_equals(
                expected, 
                dbsync.select_changes_to_run(migrations, schema_version=2))

    def test_target_version_above_schema_version(self):
        """Selects up changes above schema version upto and including target"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        expected = [
                (2, 'UP 2'), (3, 'UP 3')
        ]
        assert_equals(
                expected, 
                dbsync.select_changes_to_run(migrations, schema_version=1, target_version=3))

    def test_target_version_below_schema_version(self):
        """Selects down changes from below schema version downto but not including target"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        expected = [
                (3, 'DOWN 3'), (2, 'DOWN 2')
        ]
        assert_equals(
                expected, 
                dbsync.select_changes_to_run(migrations, schema_version=3, target_version=1))

    def test_target_version_equal_schema_version(self):
        """Selects nothing"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        expected = []
        assert_equals(
                expected, 
                dbsync.select_changes_to_run(migrations, schema_version=3, target_version=3))

