"""Minimal Stalker 2 cfg text parser / writer."""
import re

class Node:
    def __init__(self, key, value=None, header_extra=''):
        self.key = key
        self.value = value          # None for struct
        self.children = []          # list[Node]
        self.header_extra = header_extra

    @property
    def is_struct(self):
        return self.value is None

    def get(self, key):
        for c in self.children:
            if c.key == key:
                return c
        return None

    def val(self, key):
        c = self.get(key)
        return c.value if c is not None else None

    def write(self, out, depth=0):
        ind = '   ' * depth
        if self.is_struct:
            out.append(f"{ind}{self.key} : struct.begin{self.header_extra}")
            for c in self.children:
                c.write(out, depth + 1)
            out.append(f"{ind}struct.end")
        else:
            out.append(f"{ind}{self.key} = {self.value}")


BEGIN = re.compile(r'^\s*(\S+)\s*:\s*struct\.begin(.*)$')
KV = re.compile(r'^\s*([^=\s]+)\s*=\s*(.*?)\s*$')

def parse(path):
    root = Node('<root>')
    stack = [root]
    for raw in open(path, encoding='utf-8-sig', errors='replace'):
        line = raw.split('//', 1)[0].rstrip()
        if not line.strip():
            continue
        if line.strip() == 'struct.end':
            stack.pop()
            continue
        m = BEGIN.match(line)
        if m:
            n = Node(m.group(1), None, m.group(2).rstrip())
            stack[-1].children.append(n)
            stack.append(n)
            continue
        m = KV.match(line)
        if m:
            stack[-1].children.append(Node(m.group(1), m.group(2)))
            continue
        stack[-1].children.append(Node(line.strip(), ''))  # e.g. "X : removenode"
    return root
