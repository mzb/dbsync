import re


UP_ANNOTATION_RE = re.compile(r'\s*--\s*@UP\s*', re.IGNORECASE)
DOWN_ANNOTATION_RE = re.compile(r'\s*--\s*@DOWN\s*', re.IGNORECASE)

def extract_changes(sql):
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

    return {'up': up_change, 'down': down_change}
