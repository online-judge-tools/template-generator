"""
the module to find minimum format trees from sample strings

この module はサンプル文字列から直接 (つまり、フォーマット文字列を用いずに) フォーマット木を推測します。利用可能なサンプル文字列の個数がひとつしかない場合での利用が想定されています。
フォーマット木に対する評価関数を固定しておき、すべてのサンプル文字列とマッチするフォーマット木の中で最小のものを求めるという形で実装されています。

たとえば
::

    3
    1 2
    3 4 1 2
    2 4 1

および
::

    1
    2 0 8

というサンプル文字列から
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N", sequence([
            item("K_i"),
            loop(counter="j", size="K_i",
                item("A", indices=("i", "j"))
            ),
            newline(),
        ])),
    ])

のようなフォーマット木 (:any:`FormatNode`) を作ります。
この例の場合は
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N - 1", sequence([
            item("K_i"),
            loop(counter="j", size="K_i - 1",
                item("A", indices=("i", "j"))
            ),
            item("B", indices="i"),
            newline(),
        ])),
        item("L"),
        loop(counter="i", size="L",
            item("C", indices="i")
        ),
        newline(),
    ])

というフォーマット木もこれらのサンプルにマッチしますが、これは木の大きさが最小ではないので作られません。

内部のデータ構造は Haskell 風に書くと以下のような感じになります。
`LoopNode` が持つふたつの `Int` は、ループの回数を表現する変数の de Bruijn index およびその変数を修正するための -1, 0, 1 のいずれかの数です。
木の一部は構築途中である場合があります。

:: haskell
    data Token
        = IntToken Int
        | StrngToken
        | NewlineToken

    data Node m
        = LoopNode Int Int (m (Node m)) (m (Node m))
        | IntNode (m (Node m))
        | StringNode (m (Node m))
        | NewlineNode (m (Node m))
        | EOFNode

    match :: Node Maybe -> [Token] -> Maybe MatchState
    ...

    size :: Node Maybe -> Int
    size (LoopNode _ delta body next) = 1 + abs delta + size body + size next
    size (IntNode next) = 1 + size next
    size (StringNode next) = 1 + size next
    size (NewlineNode next) = 1 + size next
    size EOFNode = 1
"""

import abc
import heapq
import itertools
import string
from logging import getLogger
from typing import *

import onlinejudge_template.analyzer.node_util as node_util
from onlinejudge_template.analyzer.match import FormatMatchError, match_format
from onlinejudge_template.types import *

logger = getLogger(__name__)


class _Token(abc.ABC):
    row: int
    column: int

    def __init__(self, *, row: int, column: int):
        self.row = row
        self.column = column

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(L{self.row}C{self.column})"


class _IntToken(_Token):
    value: int

    def __init__(self, *, value: int, row: int, column: int):
        super().__init__(row=row, column=column)
        self.value = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(L{self.row}C{self.column}, value={self.value})"


class _StringToken(_Token):
    value: str

    def __init__(self, *, value: str, row: int, column: int):
        super().__init__(row=row, column=column)
        self.value = value


class _NewlineToken(_Token):
    pass


class _MatchState(NamedTuple):
    tokens: List[_Token]
    offset: int
    env: List[int]


class _MatchStop(Exception):
    def __init__(self, state: _MatchState):
        self.state = state


class _Node(abc.ABC):
    """_Node is a node similar to FormatNode but is easy to use for optimization.
    """
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    @abc.abstractmethod
    def get_tree_size(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        """
        :raises _MatchStop:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def count_placeholder(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_replaced_first_placeholder(self, node: '_Node') -> Optional['_Node']:
        raise NotImplementedError


class _PlaceholderNode(_Node):
    def get_tree_size(self) -> int:
        return 1

    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        raise _MatchStop(state)

    def count_placeholder(self) -> int:
        return 1

    def get_replaced_first_placeholder(self, node: _Node) -> _Node:
        return node


class _EOFNode(_Node):
    def get_tree_size(self) -> int:
        return 1

    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        return state

    def count_placeholder(self) -> int:
        return 0

    def get_replaced_first_placeholder(self, node: _Node) -> Optional[_Node]:
        return None


class _SimpleNonLeafNode(_Node):
    next: _Node

    def __init__(self, *, next: _Node):
        self.next = next

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(next={self.next})"

    def get_tree_size(self) -> int:
        return 1 + self.next.get_tree_size()

    def count_placeholder(self) -> int:
        return self.next.count_placeholder()

    def get_replaced_first_placeholder(self, node: _Node) -> Optional[_Node]:
        next = self.next.get_replaced_first_placeholder(node)
        if next is None:
            return None
        else:
            return self.__class__(next=next)


class _IntNode(_SimpleNonLeafNode):
    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        assert 0 <= state.offset <= len(state.tokens)
        if state.offset >= len(state.tokens):
            return None
        token = state.tokens[state.offset]
        if not isinstance(token, _IntToken):
            return None
        state = _MatchState(tokens=state.tokens, offset=state.offset + 1, env=[token.value] + state.env)
        return self.next.run_match(state)


class _StringNode(_SimpleNonLeafNode):
    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        assert 0 <= state.offset <= len(state.tokens)
        if state.offset >= len(state.tokens):
            return None
        # An int is a str. `101` is an int but `1010100101010101010100111111101010101` may be a str. `10.1` is also a str.
        if not isinstance(state.tokens[state.offset], _StringToken) and not isinstance(state.tokens[state.offset], _IntToken):
            return None
        state = _MatchState(tokens=state.tokens, offset=state.offset + 1, env=state.env)
        return self.next.run_match(state)


class _NewlineNode(_SimpleNonLeafNode):
    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        assert 0 <= state.offset <= len(state.tokens)
        if state.offset >= len(state.tokens):
            return None
        if not isinstance(state.tokens[state.offset], _NewlineToken):
            return None
        state = _MatchState(tokens=state.tokens, offset=state.offset + 1, env=state.env)
        return self.next.run_match(state)


class _LoopNode(_Node):
    index: int  # de Bruijn index
    delta: int
    body: _Node
    next: _Node

    def __init__(self, *, index: int, delta: int = 0, body: _Node, next: _Node):
        assert delta in (-1, 0, 1)
        self.index = index
        self.delta = delta
        self.body = body
        self.next = next

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(index={self.index}, delta={self.delta}, body={self.body}, next={self.next})"

    def get_tree_size(self) -> int:
        return 1 + abs(self.delta) + self.body.get_tree_size() + self.next.get_tree_size()

    def run_match(self, state: _MatchState) -> Optional[_MatchState]:
        assert 0 <= self.index < len(state.env)
        count = state.env[self.index] + self.delta
        if count <= 0:
            # loops of zero times cause some problems because some placeholders may be skipped
            return None

        for _ in range(count):
            result = self.body.run_match(state)
            if result is None:
                return None
            state = _MatchState(tokens=state.tokens, offset=result.offset, env=state.env)  # reset
        return self.next.run_match(state)

    def count_placeholder(self) -> int:
        return self.body.count_placeholder() + self.next.count_placeholder()

    def get_replaced_first_placeholder(self, node: _Node) -> Optional[_Node]:
        body = self.body.get_replaced_first_placeholder(node)
        if body is not None:
            return _LoopNode(index=self.index, delta=self.delta, body=body, next=self.next)
        else:
            next = self.next.get_replaced_first_placeholder(node)
            if next is not None:
                return _LoopNode(index=self.index, delta=self.delta, body=self.body, next=next)
            else:
                return None


class _PriorityQueue:
    _heap: List[Tuple[int, int, _Node]] = []
    _counter = itertools.count()

    def push(self, cost: int, node: _Node) -> None:
        heapq.heappush(self._heap, (cost, next(self._counter), node))

    def pop(self) -> _Node:
        """pop() returns the item which has smallest cost value.
        :raises IndexError:
        """

        _, _, node = heapq.heappop(self._heap)
        return node

    def empty(self) -> bool:
        return not self._heap


def tokenize_content(content: str) -> Iterator[_Token]:
    # The int tokens are tokens which can be used as loop sizes. Only small integers satisfy this condition.
    int_max = len(content.split()) + len(content.splitlines()) + 3

    for y, line in enumerate(content.splitlines(keepends=True)):
        words = line.split()
        for x, word in enumerate(words):
            try:
                n = int(word)
            except ValueError:
                yield _StringToken(value=word, row=y, column=x)
            else:
                if 0 <= n <= int_max:
                    yield _IntToken(value=n, row=y, column=x)
                else:
                    yield _StringToken(value=word, row=y, column=x)
        if line.endswith('\n'):  # including "\r\n"
            yield _NewlineToken(row=y, column=len(words))


def list_next_possible_node(states: List[_MatchState]) -> Iterator[_Node]:
    # validate a set of states
    assert states
    for state in states:
        assert 0 <= state.offset <= len(state.tokens)
    env_size = len(states[0].env)
    assert all([len(state.env) == env_size for state in states])

    # EOF
    yield _EOFNode()
    if all([state.offset == len(state.tokens) for state in states]):
        return

    # when some instances reach EOF but some instances don't
    if any([state.offset == len(state.tokens) for state in states]):
        return

    # when all next tokens are int tokens
    if all([isinstance(state.tokens[state.offset], _IntToken) for state in states]):
        yield _IntNode(next=_PlaceholderNode())
        for i in range(env_size):
            for delta in (-1, 0, 1):
                if all([0 <= state.env[i] + delta for state in states]):
                    yield _LoopNode(index=i, delta=delta, body=_IntNode(next=_PlaceholderNode()), next=_PlaceholderNode())
        return

    # when all next tokens are string tokens
    if all([isinstance(state.tokens[state.offset], _StringToken) or isinstance(state.tokens[state.offset], _IntToken) for state in states]):
        yield _StringNode(next=_PlaceholderNode())
        for i in range(env_size):
            for delta in (-1, 0, 1):
                if all([0 <= state.env[i] + delta for state in states]):
                    yield _LoopNode(index=i, delta=delta, body=_StringNode(next=_PlaceholderNode()), next=_PlaceholderNode())
        return

    # when all next tokens are newline tokens
    if all([isinstance(state.tokens[state.offset], _NewlineToken) for state in states]):
        yield _NewlineNode(next=_PlaceholderNode())
        # don't yield loop node here
        return

    return


def _construct_minimum_input_format_internal_tree(*, instances: List[List[_Token]], initial_env: Optional[List[List[int]]] = None, limit: int = 10000, initial_node: _Node = _PlaceholderNode()) -> Optional[_Node]:
    # init
    que = _PriorityQueue()
    que.push(initial_node.get_tree_size(), initial_node)
    while not que.empty():
        # pop
        cur = que.pop()

        # calc
        states = []
        for i, instance in enumerate(instances):
            if initial_env is not None:
                env = initial_env[i]
            else:
                env = []
            try:
                state = cur.run_match(_MatchState(tokens=instance, offset=0, env=env))
                if state is None:
                    break
                if state.offset != len(state.tokens):
                    break  # matching finished before EOF
            except _MatchStop as e:
                state = e.state
            states.append(state)
        if len(states) != len(instances):
            continue
        if all([state.offset == len(state.tokens) for state in states]) and not cur.count_placeholder():
            return cur

        # push
        for delta in list_next_possible_node(states):
            nxt = cur.get_replaced_first_placeholder(delta)
            assert nxt is not None
            que.push(nxt.get_tree_size(), nxt)

        # timeout. This function doesn't have good time complexity, so may take too long time.
        limit -= 1
        if limit < 0:
            break

    return None


class EnvItem(NamedTuple):
    name: VarName
    is_counter: bool


def _convert_to_format_node(node: _Node, *, env: List[EnvItem], used: Set[VarName], fixed_names: List[VarName]) -> FormatNode:
    def get_fresh_name() -> VarName:
        # allow using fixed name for multiple test cases
        if fixed_names:
            return fixed_names.pop()  # update the list

        for var in map(VarName, string.ascii_letters):
            if var not in used:
                return var
        else:
            assert False  # TODO: improve name assiging

    def list_indices(index: int) -> List[VarName]:
        indices = []
        for item in reversed(env[index + 1:]):
            if item.is_counter:
                indices.append(item.name)
        return indices

    if isinstance(node, _EOFNode):
        return SequenceNode(items=[])

    elif isinstance(node, _IntNode) or isinstance(node, _StringNode):
        var = get_fresh_name()
        delta: List[EnvItem] = []
        if isinstance(node, _IntNode):
            delta = [EnvItem(var, False)]
        indices = list_indices(-1)

        used.add(var)
        return SequenceNode(items=[
            ItemNode(name=var, indices=indices),
            _convert_to_format_node(node.next, env=delta + env, used=used, fixed_names=fixed_names),
        ])

    elif isinstance(node, _NewlineNode):
        return SequenceNode(items=[
            NewlineNode(),
            _convert_to_format_node(node.next, env=env, used=used, fixed_names=fixed_names),
        ])

    elif isinstance(node, _LoopNode):
        size = Expr(env[node.index].name)
        if list_indices(node.index):
            size = Expr(str(size) + '_{' + ','.join(list_indices(node.index)) + '}')
        var = get_fresh_name()

        used.add(var)
        body = _convert_to_format_node(node.body, env=[EnvItem(var, True)] + env, used=used, fixed_names=fixed_names)
        used.remove(var)
        return SequenceNode(items=[
            LoopNode(size=size, name=var, body=body),
            _convert_to_format_node(node.next, env=env, used=used, fixed_names=fixed_names),
        ])

    elif isinstance(node, _PlaceholderNode):
        assert False
    else:
        assert False


def construct_minimum_input_format_tree(*, instances: List[str], multiple_test_cases: bool = False) -> Optional[FormatNode]:
    tokenized_instances = [list(tokenize_content(instance)) for instance in instances]
    if multiple_test_cases:
        initial_node: _Node = _IntNode(next=_NewlineNode(next=_LoopNode(index=0, delta=0, body=_PlaceholderNode(), next=_EOFNode())))
    else:
        initial_node = _PlaceholderNode()
    node = _construct_minimum_input_format_internal_tree(instances=tokenized_instances, initial_node=initial_node)
    if node is None:
        return None
    format_node = _convert_to_format_node(node, env=[], used=set(), fixed_names=(multiple_test_cases and [node_util.testcases_varname] or []))
    format_node = node_util.rename_variable_nicely(format_node)
    return node_util.remove_superfluous_sequence_nodes(format_node)


def construct_minimum_output_format_tree(*, instances: List[str]) -> Optional[FormatNode]:
    return construct_minimum_input_format_tree(instances=instances)


def construct_minimum_output_format_tree_using_input_format(*, instances: List[SampleCase], input_format: FormatNode, input_variables: Dict[VarName, VarDecl], multiple_test_cases: bool) -> Optional[FormatNode]:
    # prepare environments
    minimizer_env: List[List[int]] = []
    converter_env: List[EnvItem] = []
    converter_used: Set[VarName] = set()
    try:
        for i, data in enumerate(instances):
            minimizer_env.append([])
            print()
            print(input_format, data.input.decode(), input_variables)
            print()
            print(input_format, data.input.decode(), input_variables)
            print()
            print(input_format, data.input.decode(), input_variables)
            input_values = match_format(input_format, data.input.decode(), variables=input_variables)
            for name in sorted(input_variables.keys()):
                decl = input_variables[name]
                if (decl.type == VarType.IndexInt or decl.type == VarType.ValueInt) and not decl.dims:
                    value = input_values[name][()]
                    assert isinstance(value, int)
                    minimizer_env[i].append(value)
                    if i == 0:
                        converter_env.append(EnvItem(name, False))
                if i == 0:
                    converter_used.add(name)
    except FormatMatchError as e:
        logger.debug('failed to match sample input: %s', e)
        output_samples = [case.output.decode() for case in instances]
        return construct_minimum_output_format_tree(instances=output_samples)

    # construct the tree
    tokenized_instances = [list(tokenize_content(instance.output.decode())) for instance in instances]
    initial_node: _Node = _PlaceholderNode()
    if multiple_test_cases:
        for i, item in enumerate(converter_env):
            if item.name == node_util.testcases_varname:
                initial_node = _LoopNode(index=i, delta=0, body=_PlaceholderNode(), next=_EOFNode())
                break
    node = _construct_minimum_input_format_internal_tree(instances=tokenized_instances, initial_env=minimizer_env, initial_node=initial_node)
    if node is None:
        return None

    # make format node
    format_node = _convert_to_format_node(node, env=converter_env, used=converter_used, fixed_names=[])
    format_node = node_util.rename_variable_nicely(format_node, used=converter_used)
    return node_util.remove_superfluous_sequence_nodes(format_node)
