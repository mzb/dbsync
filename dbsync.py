import re


def parse_sql_migration(sql):
    UP_ANNOTATION_RE = re.compile(r'\s*--\s*@UP\s*', re.IGNORECASE)
    DOWN_ANNOTATION_RE = re.compile(r'\s*--\s*@DOWN\s*', re.IGNORECASE)

    up_begin_idx = down_begin_idx = None
    lines = sql.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        if UP_ANNOTATION_RE.match(line): up_begin_idx = i
        if DOWN_ANNOTATION_RE.match(line): down_begin_idx = i

    if up_begin_idx is None:
        up_sql = None
    else:
        up_sql = "\n".join(lines[up_begin_idx + 1:down_begin_idx]).strip()
    if down_begin_idx is None:
        down_sql = None
    else:
        down_sql = "\n".join(lines[down_begin_idx + 1:]).strip()

    return {'up': up_sql, 'down': down_sql}
