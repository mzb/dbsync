from subprocess import Popen, PIPE
import unittest
from nose.tools import *

from dbsync import *


class ParseMigrationCode(unittest.TestCase):

    def test_up_and_down_annotations(self):
        migration = parse_migration_code('''
            -- @UP
            CREATE TABLE users
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': 'DROP TABLE users'}, migration)

    def test_one_annotation_missing(self):
        migration = parse_migration_code('''
            -- @UP
            CREATE TABLE users
        ''')
        assert_equals({'up': 'CREATE TABLE users', 'down': None}, migration, 
                'Missing @DOWN')

        migration = parse_migration_code('''
            -- @DOWN
            DROP TABLE users
        ''')
        assert_equals({'up': None, 'down': 'DROP TABLE users'}, migration, 
                'Missing @UP')

    def test_no_annotations(self):
        assert_equals({'up': None, 'down': None}, parse_migration_code(''))

    def test_annotation_like_literals_in_sql_statements(self):
        migration = parse_migration_code('''
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


class ExtractVersionFromName(unittest.TestCase):

    def test_extracts_version_from_filename(self):
        assert_equals(20130307005200, extract_version_from_name('20130307005200_foo.sql'))

    def test_extracts_version_from_filepath(self):
        assert_equals(
                20130307005200, 
                extract_version_from_name('path/to/20130307005200_foo.sql'))


class SelectApplicableChanges(unittest.TestCase):

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
        assert_equals(expected, select_applicable_changes(migrations))

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
                select_applicable_changes(migrations, schema_version=2))

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
                select_applicable_changes(migrations, schema_version=1, target_version=3))

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
                select_applicable_changes(migrations, schema_version=3, target_version=1))

    def test_target_version_equal_schema_version(self):
        """Selects nothing"""
        migrations = [
                {'version': 1, 'up': 'UP 1', 'down': 'DOWN 1'},
                {'version': 2, 'up': 'UP 2', 'down': 'DOWN 2'},
                {'version': 3, 'up': 'UP 3', 'down': 'DOWN 3'},
        ]
        assert_equals(
                [],
                select_applicable_changes(migrations, schema_version=3, target_version=3))


class ExecuteDatabaseCommand(unittest.TestCase):

    def setUp(self):
        self.db = 'sqlite3 -bail tests/test.db'
        p = Popen(self.db, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        p.communicate('''
            CREATE TABLE schema_version (version INTEGER NOT NULL);
            INSERT INTO schema_version VALUES (20130307005200);
        ''')

    def tearDown(self):
        os.remove('tests/test.db')

    def test_executes_command(self):
        result = execute_db_command(self.db, 'SELECT version FROM schema_version;')
        assert_equals('20130307005200\n', result)

    @raises(DbSyncError)
    def test_raises_error_when_command_cannot_be_executed(self):
        execute_db_command(self.db, 'FUCKED')

