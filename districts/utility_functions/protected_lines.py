"""Protected lines of the dynamic pipe sizing: lines whose pipes the sizing never changes (OpenSpec change protect-lines).
The list is kept per version in the version folder, so a child version gets it with the copied folder."""
import json
import os

FILE_NAME = 'dynamic_sizing_protected_lines.json'


def protectedLinesPath(config, version=None):
    return os.path.join(config['pathProjects'], config['projectName'], 'versions', version or config['versionName'], FILE_NAME)


def loadProtectedLines(config, version=None):
    """Line ids saved for the version; [] without a file."""
    path = protectedLinesPath(config, version)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return [int(lid) for lid in json.load(f).get('lines', [])]


def saveProtectedLines(config, lids, version=None):
    with open(protectedLinesPath(config, version), 'w', encoding='utf-8') as f:
        json.dump({'lines': [int(lid) for lid in lids]}, f, indent=1)


def parseProtectedEntries(texts):
    """(ids, invalid entries) of the list texts; empty entries are ignored, duplicates kept once in their order."""
    ids, invalid = [], []
    for text in texts:
        text = text.strip()
        if not text:
            continue
        try:
            lid = int(text)
        except ValueError:
            lid = 0
        if lid < 1:
            invalid.append(text)
        elif lid not in ids:
            ids.append(lid)
    return ids, invalid


def networkLineIds(cur, config, network):
    cur.execute("""SELECT id FROM "{}".lines WHERE network = %s;""".format(config['versionName']), (int(network),))  # nosec B608
    return {row['id'] for row in cur.fetchall()}
