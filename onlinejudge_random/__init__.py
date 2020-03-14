import math
import random as random_module
from typing import *

_r: random_module.Random = random_module  # type: ignore


def randint(a: int, b: int, *, type: str = 'auto', r: random_module.Random = _r) -> int:
    """
    randomly choose an integer
    """

    assert a <= b

    if type == 'uniform':
        return r.randint(a, b)

    elif type == 'exp':
        theta = 10
        x = r.expovariate(lambd=1 / theta)
        return min(b, a + int(x))

    elif type == 'exp-inv':
        return b - (randint(a, b, type='exp', r=r) - a)

    elif type == 'near-pow2k':
        raise NotImplementedError

    elif type == 'auto':
        table = {
            'exp': 0.5,
            'exp-inv': 0.2,
            'uniform': 0.3,
        }
        keys = list(table.keys())
        values = [table[key] for key in keys]
        type, = r.choices(keys, values)
        return randint(a, b, type=type, r=r)

    else:
        raise ValueError(f"""invalid type: {repr(type)}""")


def sequence(size: int, kind: int, *, base: int = 0, type: str = 'auto', r: random_module.Random = _r) -> List[int]:
    """
    randomly choose a sequence
    """

    if size == 0:
        return []
    assert 1 <= size
    assert 1 <= kind

    if type == 'uniform':
        return [r.randrange(kind) for _ in range(size)]

    elif type == 'almost-same':
        raise NotImplementedError

    elif type == 'almost-increasing':
        raise NotImplementedError

    elif type == 'almost-decreasing':
        raise NotImplementedError

    elif type == 'almost-permutation':
        raise NotImplementedError

    elif type == 'auto':
        table = {
            'uniform': 1,
        }
        keys = list(table.keys())
        values = [table[key] for key in keys]
        type, = r.choices(keys, values)
        return sequence(size, kind, base=base, type=type, r=r)

    else:
        raise ValueError(f"""invalid type: {repr(type)}""")


def rooted_tree_parents(nodes: int, *, base: int = 0, type: str = 'auto', r: random_module.Random = _r) -> List[int]:
    """
    randomly choose a rooted tree
    """

    assert nodes >= 1

    if type == 'uniform':
        parents = []
        for i in range(1, nodes):
            parents.append(r.randrange(i) + base)
        return parents

    elif type == 'almost-line':
        k = r.randrange(min(nodes, max(3, nodes // 10)))
        parents = []
        for i in range(1, nodes):
            if nodes - k < i:
                j = r.randrange(i)
            else:
                j = i - 1
            parents.append(j + base)
        return parents

    elif type == 'almost-star':
        k = r.randrange(min(nodes, max(3, nodes // 10)))
        parents = []
        for i in range(1, nodes):
            if k < i:
                j = k
            else:
                j = r.randrange(i)
            parents.append(j + base)
        return parents

    elif type == 'auto':
        table = {
            'uniform': 0.6,
            'almost-line': 0.2,
            'almost-star': 0.2,
        }
        keys = list(table.keys())
        values = [table[key] for key in keys]
        type, = r.choices(keys, values)
        return rooted_tree_parents(nodes, base=base, type=type, r=r)

    else:
        raise ValueError(f"""invalid type: {repr(type)}""")


def tree_edges(nodes: int, *, base: int = 0, type: str = 'auto', r: random_module.Random = _r) -> List[Tuple[int, int]]:
    """
    randomly choose a unrooted tree
    """

    sigma = list(range(nodes))
    r.shuffle(sigma)
    edges = []
    parents = rooted_tree_parents(nodes, type=type, r=r)
    for i in range(1, nodes):
        j = parents[i - 1]
        if r.random() < 0.5:
            i, j = j, i
        edges.append((sigma[i] + base, sigma[j] + base))
    r.shuffle(edges)
    return edges
