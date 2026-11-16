# coding=utf-8
"""Fluid graph of an IDA template (.idm) and the detection of the pumps that move network water
(OpenSpec change pump-power-outputs).

Nodes are (component, side); a link of the CONNECTIONS block joins two nodes when both ports are fluid ports.
A component's fluid ports form one side, except heat exchangers (liqA*/liqB*), heat pumps (evap*/cond*) and
tanks (IN/OUT vs. coil HXIN/HXOUT), whose sides are separate circuits."""
import os
import re

PUMP_TYPES = ('PUMP', 'PUMPMCTRL', 'PUMPCIRC')
PUMP_VARIABLE = 'PPUMP'

_HEADER = re.compile(r':N "([^"]+)" :T ([^\s)]+)')
_LINK = re.compile(r'\(\("([^"]+)"\s+(\([^()]*\)|[^\s()]+)\)\s+\("([^"]+)"\s+(\([^()]*\)|[^\s()]+)\)')
_VAR = re.compile(r'\(:VAR :N (\|[^|]+\||[^\s()]+)')
# network connections of a template: PMT2mux_<bundle>_<seq>_<type>_<conn> and <bundle>_<seq>_Flowmeter2
_START = re.compile(r'^(PMT2mux_\d+_\d+_\d+_\d+|\d+_\d+_Flowmeter2)$')
_FLUID_PREFIXES = ('inlet', 'outlet', 'liq', 'term', 'evap', 'cond')
_FLUID_NAMES = ('in', 'out', 'hxin', 'hxout')


def portName(port):
    """'(|term| 1)' -> ('term', '1'), '|liqA1|' -> ('liqa1', ''), 'INLET' -> ('inlet', '')."""
    words = port.strip('()').replace('|', ' ').split()
    return (words[0].lower() if words else '', words[1] if len(words) > 1 else '')


def isFluidPort(port):
    name, _ = portName(port)
    # signal ports such as OUTSIGNALLINK or INCONSUMLINK share prefixes with fluid ports
    if 'link' in name or 'signal' in name:
        return False
    return name.startswith(_FLUID_PREFIXES) or name in _FLUID_NAMES


def portSide(port):
    name, index = portName(port)
    side = re.match(r'^liq([ab])\d+$', name)
    if side:
        return side.group(1)
    if name.startswith('evap'):
        return 'evap'
    if name.startswith('cond'):
        return 'cond'
    if name in ('hxin', 'hxout'):
        return 'coil' + index
    if name in ('in', 'out'):
        return 'tank'
    return ''


def topLevelBlocks(text):
    """Top-level elements of an .idm file: every line starting with '(' at column 0 opens one."""
    blocks, current = [], []
    for line in text.splitlines():
        if line.startswith('(') and current:
            blocks.append('\n'.join(current))
            current = []
        current.append(line)
    if current:
        blocks.append('\n'.join(current))
    return blocks


def parseTemplate(text):
    """Returns ({component: type}, {component: [variables]}, [(comp_a, port_a, comp_b, port_b)])."""
    types, variables = {}, {}
    for block in topLevelBlocks(text):
        if block.startswith('(CONNECTIONS'):
            continue
        header = _HEADER.search(block.splitlines()[0])
        if header:
            types[header.group(1)] = header.group(2)
            variables[header.group(1)] = list(dict.fromkeys(_VAR.findall(block)))
    pos = text.find('(CONNECTIONS')
    links = [m.groups() for m in _LINK.finditer(text[pos:])] if pos >= 0 else []
    return types, variables, links


def networkNodes(types, links):
    """(component, side) nodes reachable from the template's network connections over fluid links."""
    adjacent = {}
    for a, pa, b, pb in links:
        if isFluidPort(pa) and isFluidPort(pb):
            na, nb = (a, portSide(pa)), (b, portSide(pb))
            adjacent.setdefault(na, set()).add(nb)
            adjacent.setdefault(nb, set()).add(na)
    todo = [node for node in adjacent if _START.match(node[0])]
    seen = set(todo)
    while todo:
        node = todo.pop()
        # inside a component, ports of the same side are one flow path
        neighbours = set(adjacent.get(node, ())) | {n for n in adjacent if n[0] == node[0] and n[1] == node[1]}
        for nxt in neighbours - seen:
            seen.add(nxt)
            todo.append(nxt)
    return seen


def detectPumps(path):
    """Network pumps of the template file `path`: ([{'component', 'type', 'variable'}], [warnings]).
    Pumps in the other .idm files of the template folder (macros) are not analysed; each gives a warning."""
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    types, _, links = parseTemplate(text)
    reached = {comp for comp, _ in networkNodes(types, links)}
    pumps = [{'component': comp, 'type': typ, 'variable': PUMP_VARIABLE}
             for comp, typ in sorted(types.items()) if typ in PUMP_TYPES and comp in reached]
    warnings = []
    folder = os.path.dirname(path)
    for name in sorted(os.listdir(folder)):
        other = os.path.join(folder, name)
        if name.lower().endswith('.idm') and os.path.normcase(other) != os.path.normcase(path):
            try:
                with open(other, encoding='utf-8-sig', errors='replace') as f:
                    macro_types, _, _ = parseTemplate(f.read())
            except OSError as e:
                warnings.append(('unreadable', name, str(e)))
                continue
            warnings += [('macro_pump', name, comp) for comp, typ in sorted(macro_types.items()) if typ in PUMP_TYPES]
    return pumps, warnings


def templateComponents(path):
    """{component: (type, [variables])} of a template file, for adding entries by hand."""
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        types, variables, _ = parseTemplate(f.read())
    return {comp: (typ, variables.get(comp, [])) for comp, typ in types.items()}
