import re


UP_ANNOTATION_RE = re.compile(r'\s*--\s*@UP\s*', re.IGNORECASE)
DOWN_ANNOTATION_RE = re.compile(r'\s*--\s*@DOWN\s*', re.IGNORECASE)

def parse_sql_migration(sql):
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

def select_changes_to_run(migrations, schema_version=None, target_version=None):
    schema_version = schema_version or 0
    target_version = target_version or max([m['version'] for m in migrations])
    selected = [];

    if target_version > schema_version:
        for migration in migrations:
           if schema_version < migration['version'] <= target_version:
               selected.append((migration['version'], migration['up']))
        selected = sorted(selected)

    elif target_version < schema_version:
        for migration in migrations:
           if schema_version >= migration['version'] > target_version:
               selected.append((migration['version'], migration['down']))
        selected = sorted(selected, reverse=True)

    return selected 
