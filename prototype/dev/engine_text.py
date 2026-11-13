"""Ordered parser for the game's line-oriented resource format.

Duplicate keys are intentional (arrays serialize this way). Values are strings,
not Python literals; braces are only structural when alone on a line.
"""
from dataclasses import dataclass, field


@dataclass
class Node:
    key: str
    value: str
    children: list | None = None


def parse(text):
    roots, stack, pending = [], [], None
    current = roots
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line == '{':
            if pending is None:
                raise ValueError(f'Unexpected opening brace at {lineno}')
            pending.children = []
            stack.append(current)
            current = pending.children
            pending = None
        elif line == '}':
            if not stack:
                raise ValueError(f'Unexpected closing brace at {lineno}')
            current = stack.pop()
            pending = None
        else:
            key, sep, value = line.partition('=')
            pending = Node(key, value) if sep else Node('', key)
            current.append(pending)
    if stack:
        raise ValueError('Unclosed resource object')
    return roots


def render(nodes, level=0):
    result = []
    for n in nodes:
        prefix = '\t' * level
        result.append(prefix + (n.key + '=' if n.key else '') + n.value)
        if n.children is not None:
            result.append(prefix + '{')
            result.extend(render(n.children, level + 1))
            result.append(prefix + '}')
    return result


def dump(nodes):
    return '\r\n'.join(render(nodes)) + '\r\n'


def get(nodes, key):
    matches = [n for n in nodes if n.key == key]
    if len(matches) != 1:
        raise ValueError(f'Expected one {key!r}, found {len(matches)}')
    return matches[0]


def scalar(key, value=''):
    return Node(key, str(value))


def obj(key, cls, children=()):
    return Node(key, cls, list(children))


def array(key, entries, count_key='Item Count'):
    return obj(key, 'Array', [scalar(count_key, len(entries)), *entries])


def constant(key, value):
    return obj(key, 'CConstant', [scalar('Constant Value', value)])


def walk(nodes):
    for n in nodes:
        yield n
        if n.children:
            yield from walk(n.children)
