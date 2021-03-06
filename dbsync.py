import re
import os
import subprocess


UP_ANNOTATION_RE = re.compile(r'\s*--\s*@UP\s*', re.IGNORECASE)
DOWN_ANNOTATION_RE = re.compile(r'\s*--\s*@DOWN\s*', re.IGNORECASE)

class DbSyncError(Exception):
    pass

def parse_migration_code(sql):
    up_annot_line_num = down_annot_line_num = None

    lines = sql.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        if UP_ANNOTATION_RE.match(line): up_annot_line_num = i
        if DOWN_ANNOTATION_RE.match(line): down_annot_line_num = i

    if up_annot_line_num is None:
        up_change = None
    else:
        up_change = "\n".join(lines[up_annot_line_num + 1:down_annot_line_num]).strip()

    if down_annot_line_num is None:
        down_change = None
    else:
        down_change = "\n".join(lines[down_annot_line_num + 1:]).strip()

    migration = {'up': up_change, 'down': down_change}
    return migration

def extract_version_from_name(name):
    match = re.match('^(\d+)', os.path.basename(name))
    if match:
        return int(match.group(0))

def select_applicable_changes(migrations, schema_version=None, target_version=None):
    schema_version = schema_version or 0
    target_version = target_version or max([m['version'] for m in migrations])
    changes = [];

    if target_version > schema_version:
        for migration in migrations:
           if schema_version < migration['version'] <= target_version:
               changes.append((migration['version'], migration['up']))
        changes = sorted(changes)

    elif target_version < schema_version:
        for migration in migrations:
           if schema_version >= migration['version'] > target_version:
               changes.append((migration['version'], migration['down']))
        changes = sorted(changes, reverse=True)

    return changes

def execute_db_command(db, command):
    p = subprocess.Popen(
            db, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            shell=True)
    stdout, stderr = p.communicate(command)

    if stderr or p.returncode != 0:
        raise DbSyncError(
                '\n'.join(["Failed to execute: %s", "stderr: %s"]) % (command, stderr))

    return stdout

def execute_change(db, change):
    version, sql = change
    execute_db_command(db, 'BEGIN;\n%s\n')
