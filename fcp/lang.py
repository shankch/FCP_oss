"""FCP-PL: the Formal Context Protocol property language.

An FCP-PL expression is evaluated at every clock cycle over interface signals,
named definitions, ghost (specification-model) state and rigid variables.

Semantics, chosen to remove the classic sources of formalization error:

* Arithmetic and comparison are *exact* integer operations; ``%`` takes a
  constant positive divisor and is floor modulo, as in Python.  Every numeric
  sub-expression carries an integer interval [lo, hi] computed statically and
  is compiled to a two's-complement wire wide enough to hold it, so
  ``count - 1`` is -1 when count is 0 (never 2**w - 1).
* Logical operators (``! && || -> <->``) accept only 1-bit (boolean) operands.
  Multi-bit values must be compared explicitly (``x != 0``).
* Bit-level operators (``~ & | ^ << >>``, slices) act on unsigned bit-vectors.
* Temporal operators are past-time only: ``prev(e[,n])``, ``rose``, ``fell``,
  ``stable``, ``changed``, ``once``, ``hist`` and ``since``.  A formula is
  therefore a function of the trace prefix, and every property compiles to a
  deterministic monitor that flags a violation exactly on the minimal bad
  prefix.  ``once``/``hist``/``since`` look back only to the most recent
  reset; ``prev`` always refers to the immediately preceding clock cycle.
* Strings and lists are bounded sequences: a length and a fixed number of
  slots, zero beyond the length.  ``len(s)``, ``s[i]`` (0 beyond the length),
  ``x in s``, ``==`` on whole sequences, string literals (``"ab"``; one
  character in a numeric context is its code) and constant lists ``[1, 2]``.
  The quantifiers ``all``, ``any``, ``count`` and ``sum`` bind a variable
  below a bound with a static maximum, ``all(i < len(s): s[i] != " ")``, and
  are expanded at compile time, so a sequence property is still a
  combinational function of the cycle.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

# A chain of definitions is compiled by recursion, a few frames per link, and
# Python's own limit of 1000 frames stops at about a hundred links.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


class FcpError(Exception):
    """Any error in an FCP artifact (parse, type, schema, semantic)."""


class ParseError(FcpError):
    pass


class FcpTypeError(FcpError):
    pass


# ----------------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------------

def signed_bits(lo: int, hi: int) -> int:
    """Smallest two's-complement width (>= 2) that holds every value in [lo, hi]."""
    w = 2
    while not (-(1 << (w - 1)) <= lo and hi <= (1 << (w - 1)) - 1):
        w += 1
    return w


@dataclass(frozen=True)
class Ty:
    kind: str          # 'bool' | 'bits' | 'num' | 'seq'
    lo: int
    hi: int
    width: int = 0     # bit-vector width ('bits'); 1 for 'bool'; packed slots ('seq')
    elem: Optional['Ty'] = None   # 'seq': the slot type; lo..hi is the length range 0..n

    @property
    def nbits(self) -> int:
        """Width of the Verilog wire that carries a value of this type."""
        if self.kind == 'bool':
            return 1
        if self.kind in ('bits', 'seq'):
            return self.width
        return signed_bits(self.lo, self.hi)

    def __str__(self) -> str:
        if self.kind == 'bool':
            return 'bool'
        if self.kind == 'bits':
            return f'bits({self.width})'
        if self.kind == 'seq':
            return f'seq({self.elem}, {self.hi})'
        return f'int[{self.lo}..{self.hi}]'


BOOL = Ty('bool', 0, 1, 1)


def BITS(w: int) -> Ty:
    if w < 1:
        raise FcpTypeError(f'bit-vector width must be >= 1, got {w}')
    return BOOL if w == 1 else Ty('bits', 0, (1 << w) - 1, w)


def NUM(lo: int, hi: int) -> Ty:
    return Ty('num', lo, hi)


def SEQ(elem: Ty, n: int) -> Ty:
    """A sequence of at most n slots of an unsigned type (a string: 8-bit slots)."""
    if n < 1 or elem.kind not in ('bits', 'bool'):
        raise FcpTypeError(f'a sequence needs n >= 1 unsigned slots, got {n} of {elem}')
    return Ty('seq', 0, n, elem.nbits * n, elem)


def seq_len_port(name: str) -> str:
    """The interface port that carries the length of sequence signal name."""
    return f'{name}__len'


# ----------------------------------------------------------------------------
# Lexer / parser (Pratt)
# ----------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
  (?P<ws>\s+)
| (?P<num>\d+'[sS]?[bBoOdDhH][0-9a-fA-F_]+ | \d[\d_]*)
| (?P<str>"(?:[^"\\\n]|\\.)*" | '(?:[^'\\\n]|\\.)*')
| (?P<id>[A-Za-z_][A-Za-z0-9_]*)
| (?P<op><->|->|\|\||&&|==|!=|<=|>=|<<|>>|[!~&|^+\-*%<>?:()\[\],])
""", re.X)


@dataclass
class Tok:
    kind: str
    text: str
    pos: int


def tokenize(src: str) -> list[Tok]:
    out, i = [], 0
    while i < len(src):
        m = _TOKEN_RE.match(src, i)
        if not m:
            raise ParseError(f'unexpected character {src[i]!r} at column {i} in: {src}')
        kind = m.lastgroup
        if kind != 'ws':
            out.append(Tok(kind, m.group(), i))
        i = m.end()
    out.append(Tok('eof', '', len(src)))
    return out


@dataclass(eq=False)
class Node:
    op: str                 # num | str | list | ref | un | bin | ite | idx | slice | call | quant
    args: tuple = ()
    val: object = None      # literal value, name, operator or function name
    width: Optional[int] = None   # sized literal width
    pos: int = 0
    ty: Optional[Ty] = None

    def __repr__(self) -> str:
        return unparse(self)


_BIN = {
    '->': (1, 'r'), '<->': (1, 'r'),
    '||': (3, 'l'), '&&': (4, 'l'),
    '|': (5, 'l'), '^': (6, 'l'), '&': (7, 'l'),
    '==': (8, 'l'), '!=': (8, 'l'), 'in': (8, 'l'),
    '<': (9, 'l'), '<=': (9, 'l'), '>': (9, 'l'), '>=': (9, 'l'),
    '<<': (10, 'l'), '>>': (10, 'l'),
    '+': (11, 'l'), '-': (11, 'l'), '*': (12, 'l'), '%': (12, 'l'),
}
_TERNARY_BP = 2
_UNARY_BP = 13
QUANT = {'all', 'any', 'count', 'sum'}       # binder forms: all(i < n: body)
_ESC = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0', '\\': '\\', '"': '"', "'": "'"}


def _unescape(body: str) -> str:
    out, i = [], 0
    while i < len(body):
        ch = body[i]
        if ch == '\\' and i + 1 < len(body):
            nx = body[i + 1]
            if nx == 'x' and i + 3 < len(body):
                out.append(chr(int(body[i + 2:i + 4], 16)))
                i += 4
                continue
            if nx not in _ESC:
                raise ParseError(f'unknown escape \\{nx} in string literal')
            out.append(_ESC[nx])
            i += 2
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _quote(text: str) -> str:
    rev = {v: k for k, v in _ESC.items() if k != "'"}
    return '"' + ''.join('\\' + rev[c] if c in rev else (c if 32 <= ord(c) < 127 else f'\\x{ord(c):02x}')
                         for c in text) + '"'


def _parse_literal(text: str) -> tuple[int, Optional[int]]:
    text = text.replace('_', '')
    if "'" not in text:
        return int(text), None
    w, rest = text.split("'", 1)
    if rest[0] in 'sS':
        rest = rest[1:]
    base = {'b': 2, 'o': 8, 'd': 10, 'h': 16}[rest[0].lower()]
    v, width = int(rest[1:], base), int(w)
    if v >= (1 << width):
        raise ParseError(f'literal {text} does not fit in {width} bits')
    return v, width


class Parser:
    def __init__(self, src: str):
        self.src = src
        self.toks = tokenize(src)
        self.i = 0

    def peek(self) -> Tok:
        return self.toks[self.i]

    def take(self, text: Optional[str] = None) -> Tok:
        t = self.toks[self.i]
        if text is not None and t.text != text:
            raise ParseError(f'expected {text!r} at column {t.pos}, found {t.text or "end"!r} in: {self.src}')
        self.i += 1
        return t

    def parse(self) -> Node:
        n = self.expr(0)
        if self.peek().kind != 'eof':
            t = self.peek()
            raise ParseError(f'unexpected {t.text!r} at column {t.pos} in: {self.src}')
        return n

    def expr(self, min_bp: int) -> Node:
        left = self.prefix()
        while True:
            t = self.peek()
            if t.text == '[':
                left = self.postfix_index(left)
                continue
            if t.text == '?' and _TERNARY_BP >= min_bp:
                self.take('?')
                a = self.expr(0)
                self.take(':')
                b = self.expr(_TERNARY_BP)
                left = Node('ite', (left, a, b), pos=t.pos)
                continue
            if (t.kind == 'op' and t.text in _BIN) or (t.kind == 'id' and t.text == 'in'):
                bp, assoc = _BIN[t.text]
                if bp < min_bp:
                    break
                self.take()
                right = self.expr(bp if assoc == 'r' else bp + 1)
                left = Node('bin', (left, right), val=t.text, pos=t.pos)
                continue
            break
        return left

    def postfix_index(self, base: Node) -> Node:
        t = self.take('[')
        hi = self.expr(0)
        if self.peek().text == ':':
            self.take(':')
            lo = self.expr(0)
            self.take(']')
            return Node('slice', (base, hi, lo), pos=t.pos)
        self.take(']')
        return Node('idx', (base, hi), pos=t.pos)

    def prefix(self) -> Node:
        t = self.take()
        if t.kind == 'num':
            v, w = _parse_literal(t.text)
            return Node('num', val=v, width=w, pos=t.pos)
        if t.kind == 'str':
            return Node('str', val=_unescape(t.text[1:-1]), pos=t.pos)
        if t.text == '[':
            items = []
            if self.peek().text != ']':
                items.append(self.expr(0))
                while self.peek().text == ',':
                    self.take(',')
                    items.append(self.expr(0))
            self.take(']')
            return Node('list', tuple(items), pos=t.pos)
        if t.kind == 'id':
            if self.peek().text == '(':
                self.take('(')
                args = []
                if self.peek().text != ')':
                    args.append(self.expr(0))
                    if self.peek().text == ':' and t.text in QUANT:
                        b = args[0]
                        if not (b.op == 'bin' and b.val == '<' and b.args[0].op == 'ref'):
                            raise ParseError(f'{t.text}(...) binds a variable: write {t.text}(i < bound: body) '
                                             f'at column {t.pos} in: {self.src}')
                        self.take(':')
                        body = self.expr(0)
                        self.take(')')
                        return Node('quant', (b.args[0], b.args[1], body), val=t.text, pos=t.pos)
                    while self.peek().text == ',':
                        self.take(',')
                        args.append(self.expr(0))
                self.take(')')
                return Node('call', tuple(args), val=t.text, pos=t.pos)
            if t.text in ('true', 'false'):
                return Node('num', val=1 if t.text == 'true' else 0, width=1, pos=t.pos)
            return Node('ref', val=t.text, pos=t.pos)
        if t.text == '(':
            n = self.expr(0)
            self.take(')')
            return n
        if t.text in ('!', '~', '-'):
            return Node('un', (self.expr(_UNARY_BP),), val=t.text, pos=t.pos)
        raise ParseError(f'unexpected {t.text or "end of input"!r} at column {t.pos} in: {self.src}')


def parse(src: str) -> Node:
    if not isinstance(src, str):
        src = str(src)
    return Parser(src).parse()


def _prec(n: Node) -> int:
    if n.op == 'bin':
        return _BIN[n.val][0]
    if n.op == 'ite':
        return _TERNARY_BP
    if n.op == 'un':
        return _UNARY_BP
    return 99


def unparse(n: Node) -> str:
    """Pretty-print with the minimal parentheses needed to preserve meaning."""
    if n.op == 'bin':
        p, assoc = _BIN[n.val]
        l, r = n.args
        ls, rs = unparse(l), unparse(r)
        if _prec(l) < p or (_prec(l) == p and (assoc == 'r' or n.val in ('->', '<->', '==', '!=', '<', '<=', '>', '>='))):
            ls = f'({ls})'
        if _prec(r) < p or (_prec(r) == p and (assoc == 'l' or n.val in ('->', '<->'))) and not (
                _prec(r) == p and r.val == n.val and n.val in ('&&', '||', '&', '|', '^', '+', '*') and False):
            rs = f'({rs})'
        return f'{ls} {n.val} {rs}'
    if n.op == 'ite':
        c, a, b = (unparse(x) for x in n.args)
        if _prec(n.args[0]) <= _TERNARY_BP:
            c = f'({c})'
        return f'{c} ? {a} : {b}'
    if n.op == 'un':
        a = unparse(n.args[0])
        return f'{n.val}{a}' if _prec(n.args[0]) >= _UNARY_BP else f'{n.val}({a})'
    return _unparse_atom(n)


def _unparse_atom(n: Node) -> str:
    if n.op == 'num':
        return f"{n.width}'d{n.val}" if n.width and n.width > 1 else (
            ('true' if n.val else 'false') if n.width == 1 else str(n.val))
    if n.op == 'ref':
        return str(n.val)
    if n.op == 'str':
        return _quote(n.val)
    if n.op == 'list':
        return '[' + ', '.join(unparse(a) for a in n.args) + ']'
    if n.op == 'quant':
        v, b, body = n.args
        return f'{n.val}({v.val} < {unparse(b)}: {unparse(body)})'
    if n.op == 'un':
        return f'{n.val}{_wrap(n.args[0])}'
    if n.op == 'bin':
        return f'{_wrap(n.args[0])} {n.val} {_wrap(n.args[1])}'
    if n.op == 'ite':
        return f'{_wrap(n.args[0])} ? {_wrap(n.args[1])} : {_wrap(n.args[2])}'
    if n.op == 'idx':
        return f'{_wrap(n.args[0])}[{unparse(n.args[1])}]'
    if n.op == 'slice':
        return f'{_wrap(n.args[0])}[{unparse(n.args[1])}:{unparse(n.args[2])}]'
    if n.op == 'call':
        return f'{n.val}(' + ', '.join(unparse(a) for a in n.args) + ')'
    raise AssertionError(n.op)


def _wrap(n: Node) -> str:
    s = unparse(n)
    return f'({s})' if n.op in ('bin', 'ite') else s


def refs(n: Node) -> set[str]:
    """All identifiers referenced by an expression (not following defs);
    a quantifier's own variable is not a reference."""
    out = set()
    if n.op == 'ref':
        out.add(n.val)
    if n.op == 'quant':
        return refs(n.args[1]) | (refs(n.args[2]) - {n.args[0].val})
    for a in n.args:
        out |= refs(a)
    return out


def calls(n: Node) -> set[str]:
    out = {n.val} if n.op == 'call' else set()
    for a in n.args:
        out |= calls(a)
    return out


# ----------------------------------------------------------------------------
# Constant evaluation (parameters, widths, pattern arguments)
# ----------------------------------------------------------------------------

def clog2(v: int) -> int:
    return 0 if v <= 1 else (v - 1).bit_length()


def const_eval(src, params: dict[str, int]) -> int:
    """Evaluate a parameter expression such as ``WIDTH`` or ``clog2(DEPTH+1)``."""
    if isinstance(src, bool):
        return int(src)
    if isinstance(src, int):
        return src
    n = parse(str(src))

    def ev(n: Node) -> int:
        if n.op == 'num':
            return n.val
        if n.op == 'ref':
            if n.val not in params:
                raise FcpError(f'unknown parameter {n.val!r} in constant expression {src!r}')
            return params[n.val]
        if n.op == 'un':
            v = ev(n.args[0])
            return {'-': -v, '!': int(not v), '~': ~v}[n.val]
        if n.op == 'bin':
            a, b = ev(n.args[0]), ev(n.args[1])
            ops: dict[str, Callable[[int, int], int]] = {
                '+': lambda x, y: x + y, '-': lambda x, y: x - y, '*': lambda x, y: x * y,
                '<<': lambda x, y: x << y, '>>': lambda x, y: x >> y,
                '==': lambda x, y: int(x == y), '!=': lambda x, y: int(x != y),
                '<': lambda x, y: int(x < y), '<=': lambda x, y: int(x <= y),
                '>': lambda x, y: int(x > y), '>=': lambda x, y: int(x >= y),
                '&&': lambda x, y: int(bool(x) and bool(y)), '||': lambda x, y: int(bool(x) or bool(y)),
                '&': lambda x, y: x & y, '|': lambda x, y: x | y, '^': lambda x, y: x ^ y,
            }
            if n.val not in ops:
                raise FcpError(f'operator {n.val} not allowed in constant expression {src!r}')
            return ops[n.val](a, b)
        if n.op == 'ite':
            return ev(n.args[1]) if ev(n.args[0]) else ev(n.args[2])
        if n.op == 'call':
            args = [ev(a) for a in n.args]
            fns = {'clog2': clog2, 'max': max, 'min': min, 'pow2': lambda x: 1 << x}
            if n.val not in fns:
                raise FcpError(f'function {n.val} not allowed in constant expression {src!r}')
            return fns[n.val](*args)
        raise FcpError(f'not a constant expression: {src!r}')

    return ev(n)


# ----------------------------------------------------------------------------
# Symbols and scopes
# ----------------------------------------------------------------------------

@dataclass
class Sym:
    name: str
    kind: str                     # signal | def | ghost | rigid | param | const
    ty: Ty
    node: Optional[Node] = None   # body of a def
    value: Optional[int] = None   # param / bound constant


def lookback(n: Node, syms: dict[str, Sym], seen: Optional[set] = None, memo: Optional[dict] = None) -> int:
    """Largest number of cycles an expression looks back with prev-family operators.
    A definition is measured once (memo): a chain of definitions that each
    name the one before several times has exponentially many paths."""
    seen = seen if seen is not None else set()
    memo = memo if memo is not None else {}
    if n.op == 'ref':
        s = syms.get(n.val)
        if s is not None and s.kind == 'def' and n.val not in seen:
            if n.val not in memo:
                memo[n.val] = lookback(s.node, syms, seen | {n.val}, memo)
            return memo[n.val]
        return 0
    inner = max([lookback(a, syms, seen, memo) for a in n.args], default=0)
    if n.op == 'call' and n.val == 'prev':
        k = 1
        if len(n.args) == 2 and n.args[1].op == 'num':
            k = n.args[1].val
        elif len(n.args) == 2:                      # a depth over parameters: prev(x, DEPTH - 1)
            try:
                k = const_eval(unparse(n.args[1]), {x: s.value for x, s in syms.items()
                                                    if s.kind == 'param' and s.value is not None})
            except FcpError:
                k = 1                               # not a constant: the compiler rejects it
        return k + lookback(n.args[0], syms, seen, memo)
    if n.op == 'call' and n.val in ('rose', 'fell', 'stable', 'changed'):
        return 1 + inner
    return inner


@dataclass
class Scope:
    """Name resolution context.  ``bind`` maps rigid-variable names to
    constants; it is used to expand universally quantified properties into
    deterministic conjunctions for use in assumption position."""
    syms: dict[str, Sym]
    bind: dict[str, int] = field(default_factory=dict)
    key: str = ''

    def lookup(self, name: str, pos: int = 0) -> Sym:
        if name in self.bind:
            v = self.bind[name]
            s = self.syms.get(name)
            return Sym(name, 'const', s.ty if s is not None and s.kind == 'rigid' else NUM(v, v), value=v)
        if name not in self.syms:
            raise FcpTypeError(f'unknown identifier {name!r}')
        return self.syms[name]

    def with_binding(self, bind: dict[str, int]) -> 'Scope':
        b = dict(self.bind)
        b.update(bind)
        key = ','.join(f'{k}={v}' for k, v in sorted(b.items()))
        return Scope(self.syms, b, key)


TEMPORAL = {'prev', 'rose', 'fell', 'stable', 'changed', 'once', 'hist', 'since'}
CHARS = {'isdigit': [(48, 57)], 'isalpha': [(65, 90), (97, 122)], 'isalnum': [(48, 57), (65, 90), (97, 122)],
         'islower': [(97, 122)], 'isupper': [(65, 90)], 'isspace': [(9, 13), (32, 32)]}
FUNCS = TEMPORAL | {'onehot', 'onehot0', 'countones', 'any', 'all', 'min', 'max', 'zext', 'len',
                    'lower', 'upper'} | set(CHARS)
QMAX = 256                     # largest static bound of a quantifier


def lit_ty(v: int) -> Ty:
    return NUM(v, v)


# ----------------------------------------------------------------------------
# Verilog emission helpers
# ----------------------------------------------------------------------------

def vdecl(ty: Ty) -> str:
    if ty.kind == 'bool':
        return ''
    if ty.kind in ('bits', 'seq'):
        return f'[{ty.width - 1}:0] '
    return f'signed [{ty.nbits - 1}:0] '


WIDE = 4096     # the longest literal written as one token


def vbits(v: int, w: int) -> str:
    """The w-bit literal of v, 0 <= v < 2**w.  A literal wider than WIDE is
    written as a concatenation of pieces, a run of equal bits as a
    replication: yosys cannot read one token of 65,537 digits (its scanner's
    buffer is fixed), and a shift by a 16-bit amount makes such a constant."""
    s = f'{v:0{w}b}'
    if w <= WIDE:
        return f"{w}'b{s}"
    parts = []
    for i in range(0, w, WIDE):
        p = s[i:i + WIDE]
        parts.append(f"{{{len(p)}{{1'b{p[0]}}}}}" if p.count(p[0]) == len(p) else f"{len(p)}'b{p}")
    return '{' + ', '.join(parts) + '}'


def vconst(v: int, ty: Ty) -> str:
    """A Verilog literal of value v in the representation of ty."""
    w = ty.nbits
    if ty.kind == 'num':
        return f"$signed({vbits(v & ((1 << w) - 1), w)})"
    if v < 0 or v >= (1 << w):
        raise FcpTypeError(f'constant {v} does not fit in {w} unsigned bits')
    return vbits(v, w) if w > 1 else ("1'b1" if v else "1'b0")


@dataclass
class Val:
    """A compiled value: a Verilog identifier (or literal) and its type."""
    v: str
    ty: Ty
    const: Optional[int] = None


@dataclass
class SeqVal(Val):
    """A compiled sequence: v is the packed canonical data (slot k in bits
    [k*w + w - 1 : k*w], zero beyond the length), ln its length (int 0..n).
    const, for a literal, is the tuple of its elements."""
    ln: Optional[Val] = None


class Builder:
    """Accumulates the body of a monitor module.

    Every expression node is materialised as an explicitly typed wire, which
    sidesteps Verilog's context-dependent width and signedness rules.
    """

    def __init__(self, rst_active: str = 'rst_active'):
        self.decls: list[str] = []
        self.seq: list[str] = []          # statements inside always @(posedge clk)
        self.n = 0
        self.rst = rst_active
        self.cache: dict[tuple, Val] = {}
        self.max_prev = 0                 # deepest prev() nesting used anywhere
        self.ghost_hook: Optional[Callable[[str, Scope], Val]] = None
        self.seq_cache: dict[str, SeqVal] = {}
        self.elem_cache: dict[tuple[str, int], Val] = {}

    # -- naming --------------------------------------------------------------
    def fresh(self, prefix: str = '_e') -> str:
        self.n += 1
        return f'{prefix}{self.n}'

    def wire(self, ty: Ty, expr: str, name: Optional[str] = None, comment: str = '') -> Val:
        name = name or self.fresh()
        c = f'  // {comment}' if comment else ''
        self.decls.append(f'  wire {vdecl(ty)}{name} = {expr};{c}')
        return Val(name, ty)

    def reg(self, ty: Ty, name: Optional[str] = None, init: Optional[int] = None, comment: str = '') -> str:
        name = name or self.fresh('_r')
        c = f'  // {comment}' if comment else ''
        ini = f' = {vconst(init, ty)}' if init is not None else ''
        self.decls.append(f'  reg {vdecl(ty)}{name}{ini};{c}')
        return name

    # -- conversions ---------------------------------------------------------
    def as_num(self, x: Val, w: int, trunc: bool = False) -> str:
        """Expression for x as a w-bit signed two's-complement value.

        trunc allows w to be narrower than x: only sound for + - * whose exact
        result is known to fit in w bits (arithmetic modulo 2**w is a ring
        homomorphism), never for comparisons."""
        if x.const is not None:
            return f"$signed({vbits(x.const & ((1 << w) - 1), w)})"
        t = x.ty
        if t.kind == 'num':
            k = w - t.nbits
            if k < 0:
                if not trunc:
                    raise AssertionError('narrowing')
                return f'$signed({x.v}[{w - 1}:0])'
            return x.v if k == 0 else f'$signed({{{{{k}{{{x.v}[{t.nbits - 1}]}}}}, {x.v}}})'
        width = t.nbits
        k = w - width
        if k <= 0:
            if not trunc:
                raise AssertionError('unsigned value needs a sign bit')
            return f'$signed({x.v}[{w - 1}:0])'
        return f"$signed({{{k}'b0, {x.v}}})"

    def as_bits(self, x: Val, w: int) -> str:
        if x.const is not None:
            if x.const < 0 or x.const >= (1 << w):
                raise FcpTypeError(f'constant {x.const} does not fit in {w} bits')
            return vconst(x.const, BITS(w))
        if x.ty.kind == 'num':
            raise FcpTypeError('bit-level operator applied to an integer-valued expression; '
                               'only signals, slices and bit-level results are bit-vectors')
        if x.ty.width == w:
            return x.v
        if x.ty.width > w:
            raise FcpTypeError(f'bit-vector of width {x.ty.width} used where width {w} expected')
        return f"{{{w - x.ty.width}'b0, {x.v}}}"

    def const(self, v: int, ty: Optional[Ty] = None) -> Val:
        ty = ty or lit_ty(v)
        return Val(vconst(v, ty), ty, const=v)

    # -- values --------------------------------------------------------------
    def cmpv(self, a: Val, b: Val, o: str) -> Val:
        if a.const is not None and b.const is not None:
            x, y = a.const, b.const
            r = {'==': x == y, '!=': x != y, '<': x < y, '<=': x <= y, '>': x > y, '>=': x >= y}[o]
            return self.const(int(r), BOOL)
        if o in ('==', '!=') and a.ty.kind != 'num' and b.ty.kind != 'num' and \
                a.ty.nbits == b.ty.nbits and a.const is None and b.const is None:
            return self.wire(BOOL, f'{a.v} {o} {b.v}')
        w = max(signed_bits(a.ty.lo, a.ty.hi), signed_bits(b.ty.lo, b.ty.hi))
        # statically decided comparisons are folded (and reported by lint)
        return self.wire(BOOL, f'{self.as_num(a, w)} {o} {self.as_num(b, w)}')

    def andv(self, vals: list[Val]) -> Val:
        vals = [v for v in vals if v.const != 1]
        if any(v.const == 0 for v in vals):
            return self.const(0, BOOL)
        if not vals:
            return self.const(1, BOOL)
        return vals[0] if len(vals) == 1 else self.wire(BOOL, ' && '.join(v.v for v in vals))

    def orv(self, vals: list[Val]) -> Val:
        vals = [v for v in vals if v.const != 0]
        if any(v.const == 1 for v in vals):
            return self.const(1, BOOL)
        if not vals:
            return self.const(0, BOOL)
        return vals[0] if len(vals) == 1 else self.wire(BOOL, ' || '.join(v.v for v in vals))

    def notv(self, v: Val) -> Val:
        return self.const(1 - v.const, BOOL) if v.const is not None else self.wire(BOOL, f'!{v.v}')

    def bool01(self, v: Val) -> Val:
        if v.ty.kind != 'bool':
            return v
        return self.const(v.const) if v.const is not None else self.wire(NUM(0, 1), f"$signed({{1'b0, {v.v}}})")

    def ite_num(self, c: Val, a: Val, b: Val) -> Val:
        if c.const is not None:
            return a if c.const else b
        a, b = self.bool01(a), self.bool01(b)
        ty = NUM(min(a.ty.lo, b.ty.lo), max(a.ty.hi, b.ty.hi))
        return self.wire(ty, f'{c.v} ? {self.as_num(a, ty.nbits)} : {self.as_num(b, ty.nbits)}')

    def addv(self, vals: list[Val]) -> Val:
        vals = [self.bool01(v) for v in vals]
        k = sum(v.const for v in vals if v.const is not None)
        rest = [v for v in vals if v.const is None]
        if not rest:
            return self.const(k)
        lo, hi = k + sum(v.ty.lo for v in rest), k + sum(v.ty.hi for v in rest)
        ty = NUM(lo, hi)
        w = ty.nbits
        terms = [self.as_num(v, w, trunc=True) for v in rest] + ([f"$signed({w}'d{k})"] if k > 0 else []) + \
            ([f"-$signed({w}'d{-k})"] if k < 0 else [])
        return self.wire(ty, ' + '.join(terms))

    # -- sequences -----------------------------------------------------------
    def scalar(self, x: Val, n: Node) -> Val:
        """x where a number or a condition is expected: a one-character string
        literal is its code, any other sequence is a type error."""
        if not isinstance(x, SeqVal):
            return x
        if x.const is not None and len(x.const) == 1:
            return self.const(x.const[0])
        raise FcpTypeError(f'{unparse(n)} is a sequence ({x.ty}) where a number or a condition is expected')

    def num(self, n: Node, sc: Scope) -> Val:
        return self.scalar(self.compile(n, sc), n)

    def as_bool(self, x: Val, n: Node, what: str) -> Val:
        x = self.scalar(x, n)
        if x.ty.kind != 'bool':
            if x.const is not None and x.const in (0, 1):
                return self.const(x.const, BOOL)
            raise FcpTypeError(f'{what} must be boolean (1-bit) but {unparse(n)} has type {x.ty}; '
                               f'compare it explicitly, e.g. ({unparse(n)}) != 0')
        return x

    def seq_const(self, codes, et: Ty, n: int = 0) -> SeqVal:
        codes = tuple(codes)
        n = max(1, len(codes), n)
        w = et.nbits
        for c in codes:
            if not 0 <= c < (1 << w):
                raise FcpTypeError(f'sequence element {c} does not fit in {w} unsigned bits')
        data = sum(c << (k * w) for k, c in enumerate(codes))
        return SeqVal(f"{n * w}'h{data:x}", SEQ(et, n), const=codes, ln=self.const(len(codes)))

    def pack(self, elems: list[Val], ln: Val, et: Ty) -> SeqVal:
        """A sequence from its slots (each zero beyond ln) and its length."""
        if ln.const is not None and all(e.const is not None for e in elems):
            return self.seq_const([e.const for e in elems[:ln.const]], et, len(elems))
        w = et.nbits
        parts = [self.as_bits(e, w) for e in reversed(elems)]
        v = self.wire(SEQ(et, len(elems)), '{' + ', '.join(parts) + '}' if len(parts) > 1 else parts[0])
        sv = SeqVal(v.v, v.ty, ln=ln)
        for k, e in enumerate(elems):
            self.elem_cache[(sv.v, k)] = e
        return sv

    def seq_signal(self, name: str, ty: Ty) -> SeqVal:
        """An interface sequence in canonical form: the length port clamped to
        n and every slot at or beyond the length read as zero, whatever the
        ports carry."""
        if name in self.seq_cache:
            return self.seq_cache[name]
        n, et = ty.hi, ty.elem
        w, lw = et.nbits, max(1, clog2(n + 1))
        lty = NUM(0, n)
        raw = self.as_num(Val(seq_len_port(name), BITS(lw)), lty.nbits)
        top = vconst(n, lty)
        ln = self.wire(lty, f'({raw} > {top}) ? {top} : {raw}' if (1 << lw) - 1 > n else raw, comment=f'len({name})')
        elems = []
        for k in range(n):
            sl = f'{name}[{k * w + w - 1}:{k * w}]' if ty.width > 1 else name
            elems.append(self.wire(et, f'({vconst(k, lty)} < {ln.v}) ? {sl} : {vconst(0, et)}'))
        sv = self.pack(elems, ln, et)
        self.seq_cache[name] = sv
        return sv

    def elem(self, sv: SeqVal, k: int) -> Val:
        """Slot k of a sequence: 0 at or beyond the length."""
        if sv.const is not None:
            return self.const(sv.const[k] if 0 <= k < len(sv.const) else 0)
        if not 0 <= k < sv.ty.hi:
            return self.const(0)
        key = (sv.v, k)
        if key not in self.elem_cache:
            w = sv.ty.elem.nbits
            self.elem_cache[key] = self.wire(sv.ty.elem, f'{sv.v}[{k * w + w - 1}:{k * w}]')
        return self.elem_cache[key]

    def seq_eq(self, a: SeqVal, b: SeqVal) -> Val:
        # both canonical: equal lengths and equal slots below the shorter capacity
        n = min(a.ty.hi, b.ty.hi)
        return self.andv([self.cmpv(a.ln, b.ln, '==')] +
                         [self.cmpv(self.elem(a, k), self.elem(b, k), '==') for k in range(n)])

    def seq_ite(self, c: Val, a: SeqVal, b: SeqVal) -> SeqVal:
        if c.const is not None:
            return a if c.const else b
        n = max(a.ty.hi, b.ty.hi)
        et = BITS(max(a.ty.elem.nbits, b.ty.elem.nbits))
        w = et.nbits
        elems = [self.wire(et, f'{c.v} ? {self.as_bits(self.elem(a, k), w)} : {self.as_bits(self.elem(b, k), w)}')
                 for k in range(n)]
        return self.pack(elems, self.ite_num(c, a.ln, b.ln), et)

    def member(self, a: Val, b: Val, n: Node) -> Val:
        if not isinstance(b, SeqVal):
            raise FcpTypeError(f'the right operand of in must be a string or a list in {unparse(n)}')
        if isinstance(a, SeqVal) and not (a.const is not None and len(a.const) == 1):
            raise FcpTypeError(f'substring tests are not supported in {unparse(n)}: '
                               f'quantify over positions with any(i < len(s): ...)')
        a = self.scalar(a, n.args[0])
        if b.const is not None:
            return self.orv([self.cmpv(a, self.const(c), '==') for c in sorted(set(b.const))])
        return self.orv([self.andv([self.cmpv(self.const(k), b.ln, '<'), self.cmpv(a, self.elem(b, k), '==')])
                         for k in range(b.ty.hi)])

    def _quant(self, n: Node, sc: Scope) -> Val:
        f, (var, bnd, body) = n.val, n.args
        bound = self.num(bnd, sc)
        if bound.ty.kind == 'bool':
            raise FcpTypeError(f'the bound of {f}() must be an integer in {unparse(n)}')
        top = bound.const if bound.const is not None else bound.ty.hi
        if top > QMAX:
            raise FcpTypeError(f'{f}(): the bound {unparse(bnd)} can reach {top}; '
                               f'a quantifier ranges over at most {QMAX} values')
        terms = []
        for k in range(max(0, top)):
            g = self.const(1, BOOL) if k < bound.ty.lo else self.cmpv(self.const(k), bound, '<')
            if g.const == 0:
                continue
            x = self.compile(body, sc.with_binding({var.val: k}))
            x = self.as_bool(x, body, f'the body of {f}()') if f != 'sum' else self.bool01(self.scalar(x, body))
            terms.append((g, x))
        if f == 'all':
            return self.andv([x if g.const == 1 else self.orv([self.notv(g), x]) for g, x in terms])
        if f == 'any':
            return self.orv([x if g.const == 1 else self.andv([g, x]) for g, x in terms])
        if f == 'count':
            return self.addv([self.bool01(self.andv([g, x])) for g, x in terms])
        return self.addv([x if g.const == 1 else self.ite_num(g, x, self.const(0)) for g, x in terms])

    # -- main entry ----------------------------------------------------------
    def compile(self, n: Node, scope: Scope) -> Val:
        key = (id(n), scope.key)
        if key in self.cache:
            return self.cache[key]
        v = self._compile(n, scope)
        self.cache[key] = v
        n.ty = v.ty
        return v

    def _compile(self, n: Node, sc: Scope) -> Val:
        op = n.op
        if op == 'num':
            if n.width:
                return self.const(n.val, BITS(n.width)) if n.width > 1 else self.const(n.val, BOOL)
            return self.const(n.val)
        if op == 'str':
            if any(ord(c) > 255 for c in n.val):
                raise FcpTypeError(f'string literal {unparse(n)} has a character beyond code 255')
            return self.seq_const([ord(c) for c in n.val], BITS(8))
        if op == 'list':
            items = [self.num(a, sc) for a in n.args]
            if any(x.const is None or x.const < 0 for x in items):
                raise FcpTypeError(f'list literals hold non-negative constants only: {unparse(n)}')
            return self.seq_const([x.const for x in items], BITS(max([1] + [x.const.bit_length() for x in items])))
        if op == 'quant':
            return self._quant(n, sc)
        if op == 'ref':
            s = sc.lookup(n.val, n.pos)
            if s.kind in ('param', 'const'):
                return self.const(s.value, s.ty if s.kind == 'const' and s.ty.kind != 'num' else None)
            if s.kind == 'def':
                return self.compile(s.node, sc)
            if s.kind == 'ghost':
                assert self.ghost_hook is not None
                return self.ghost_hook(s.name, sc)
            if s.ty.kind == 'seq':
                return self.seq_signal(s.name, s.ty)
            return Val(s.name if s.kind == 'signal' else f'rg_{s.name}', s.ty)
        if op == 'un':
            return self._unary(n, sc)
        if op == 'bin':
            return self._binary(n, sc)
        if op == 'ite':
            c = self.boolean(n.args[0], sc, 'condition of ?:')
            a, b = self.compile(n.args[1], sc), self.compile(n.args[2], sc)
            if isinstance(a, SeqVal) and isinstance(b, SeqVal):
                return self.seq_ite(c, a, b)
            a, b = self.scalar(a, n.args[1]), self.scalar(b, n.args[2])
            if c.const is not None:
                return a if c.const else b
            if a.ty.kind == 'bool' and b.ty.kind == 'bool':
                return self.wire(BOOL, f'{c.v} ? {a.v} : {b.v}')
            if a.ty.kind == 'bits' and b.ty.kind == 'bits' and a.ty.width == b.ty.width:
                return self.wire(a.ty, f'{c.v} ? {a.v} : {b.v}')
            ty = NUM(min(a.ty.lo, b.ty.lo), max(a.ty.hi, b.ty.hi))
            return self.wire(ty, f'{c.v} ? {self.as_num(a, ty.nbits)} : {self.as_num(b, ty.nbits)}')
        if op == 'idx':
            base = self.compile(n.args[0], sc)
            if isinstance(base, SeqVal):
                return self._element(base, self.num(n.args[1], sc))
            if base.ty.kind != 'bits':
                raise FcpTypeError(f'bit-select applied to non-bit-vector ({base.ty}) in {unparse(n)}')
            ix = self.num(n.args[1], sc)
            if ix.const is not None:
                if not 0 <= ix.const < base.ty.width:
                    raise FcpTypeError(f'bit index {ix.const} out of range for {base.ty} in {unparse(n)}')
                return self.wire(BOOL, f'{base.v}[{ix.const}]')
            if ix.ty.lo < 0:
                raise FcpTypeError(f'bit index may be negative in {unparse(n)}')
            w = max(1, ix.ty.hi.bit_length())
            idx = f'{ix.v}[{w - 1}:0]' if ix.ty.kind == 'num' else ix.v
            if ix.ty.hi < base.ty.width:
                return self.wire(BOOL, f'{base.v}[{idx}]')
            return self.wire(BOOL, f'({self.as_num(ix, ix.ty.nbits if ix.ty.kind == "num" else ix.ty.nbits + 1)} < '
                                   f'{base.ty.width}) ? {base.v}[{idx}] : 1\'b0')
        if op == 'slice':
            base = self.compile(n.args[0], sc)
            hi, lo = self.compile(n.args[1], sc), self.compile(n.args[2], sc)
            if hi.const is None or lo.const is None:
                raise FcpTypeError(f'slice bounds must be constant in {unparse(n)}')
            if base.ty.kind != 'bits' or not (0 <= lo.const <= hi.const < base.ty.width):
                raise FcpTypeError(f'invalid slice [{hi.const}:{lo.const}] of {base.ty} in {unparse(n)}')
            return self.wire(BITS(hi.const - lo.const + 1), f'{base.v}[{hi.const}:{lo.const}]')
        if op == 'call':
            return self._call(n, sc)
        raise AssertionError(op)

    def _element(self, base: SeqVal, ix: Val) -> Val:
        """base[ix]: 0 when ix is outside the sequence."""
        if ix.const is not None:
            return self.elem(base, ix.const)
        n, et = base.ty.hi, base.ty.elem
        lo, hi = max(0, ix.ty.lo), min(n - 1, ix.ty.hi)
        if hi < lo:
            return self.const(0)
        w = max(signed_bits(ix.ty.lo, ix.ty.hi), signed_bits(0, n))
        e = vconst(0, et)
        for k in range(hi, lo - 1, -1):
            e = f"({self.as_num(ix, w)} == $signed({w}'d{k})) ? {self.as_bits(self.elem(base, k), et.nbits)} : {e}"
        return self.wire(et, e)

    def boolean(self, n: Node, sc: Scope, what: str) -> Val:
        v = self.num(n, sc)
        if v.ty.kind != 'bool':
            if v.const is not None and v.const in (0, 1):
                return self.const(v.const, BOOL)
            raise FcpTypeError(f'{what} must be boolean (1-bit) but {unparse(n)} has type {v.ty}; '
                               f'compare it explicitly, e.g. ({unparse(n)}) != 0')
        return v

    def _unary(self, n: Node, sc: Scope) -> Val:
        if n.val == '!':
            a = self.boolean(n.args[0], sc, 'operand of !')
            if a.const is not None:
                return self.const(1 - a.const, BOOL)
            return self.wire(BOOL, f'!{a.v}')
        a = self.num(n.args[0], sc)
        if n.val == '~':
            if a.ty.kind == 'num':
                raise FcpTypeError(f'~ applied to integer-valued {unparse(n.args[0])}')
            return self.wire(a.ty, f'~{a.v}')
        # unary minus
        if a.const is not None:
            return self.const(-a.const)
        ty = NUM(-a.ty.hi, -a.ty.lo)
        return self.wire(ty, f'-{self.as_num(a, ty.nbits, trunc=True)}')

    def _binary(self, n: Node, sc: Scope) -> Val:
        o = n.val
        if o in ('&&', '||', '->', '<->'):
            a = self.boolean(n.args[0], sc, f'left operand of {o}')
            b = self.boolean(n.args[1], sc, f'right operand of {o}')
            if a.const is not None and b.const is not None:
                x, y = a.const, b.const
                r = {'&&': x & y, '||': x | y, '->': (1 - x) | y, '<->': int(x == y)}[o]
                return self.const(r, BOOL)
            expr = {'&&': f'{a.v} && {b.v}', '||': f'{a.v} || {b.v}',
                    '->': f'!{a.v} || {b.v}', '<->': f'{a.v} == {b.v}'}[o]
            return self.wire(BOOL, expr)
        a, b = self.compile(n.args[0], sc), self.compile(n.args[1], sc)
        if o == 'in':
            return self.member(a, b, n)
        if o in ('==', '!=') and isinstance(a, SeqVal) and isinstance(b, SeqVal):
            eq = self.seq_eq(a, b)
            return eq if o == '==' else self.notv(eq)
        a, b = self.scalar(a, n.args[0]), self.scalar(b, n.args[1])
        if o in ('&', '|', '^'):
            if a.ty.kind == 'bool' and b.ty.kind == 'bool':
                return self.wire(BOOL, f'{a.v} {o} {b.v}')
            if a.const is not None and b.const is None:
                a, b = b, a
            if a.ty.kind == 'num':
                raise FcpTypeError(f'bit-level {o} needs bit-vector operands in {unparse(n)}')
            w = a.ty.nbits if b.const is not None else max(a.ty.nbits, b.ty.nbits)
            return self.wire(BITS(w), f'{self.as_bits(a, w)} {o} {self.as_bits(b, w)}')
        if o in ('==', '!=', '<', '<=', '>', '>='):
            return self.cmpv(a, b, o)
        if o in ('+', '-', '*'):
            if a.const is not None and b.const is not None:
                return self.const({'+': a.const + b.const, '-': a.const - b.const, '*': a.const * b.const}[o])
            if o == '+':
                ty = NUM(a.ty.lo + b.ty.lo, a.ty.hi + b.ty.hi)
            elif o == '-':
                ty = NUM(a.ty.lo - b.ty.hi, a.ty.hi - b.ty.lo)
            else:
                ps = [a.ty.lo * b.ty.lo, a.ty.lo * b.ty.hi, a.ty.hi * b.ty.lo, a.ty.hi * b.ty.hi]
                ty = NUM(min(ps), max(ps))
            w = ty.nbits
            return self.wire(ty, f'{self.as_num(a, w, trunc=True)} {o} {self.as_num(b, w, trunc=True)}')
        if o == '%':
            if b.const is None or b.const < 1:
                raise FcpTypeError(f'% needs a constant positive divisor in {unparse(n)}')
            if a.const is not None:
                return self.const(a.const % b.const)
            w = max(signed_bits(a.ty.lo, a.ty.hi), signed_bits(b.const, b.const))
            if a.ty.lo < 0:
                # floor modulo, as in Python: the result is in 0 .. divisor-1
                r = self.wire(NUM(-(b.const - 1), b.const - 1), f'{self.as_num(a, w)} % {self.as_num(b, w)}')
                ty = NUM(0, b.const - 1)
                return self.wire(ty, f'({r.v} < 0) ? {self.as_num(r, ty.nbits + 1, trunc=True)} + '
                                     f'{self.as_num(b, ty.nbits + 1)} : {self.as_num(r, ty.nbits + 1, trunc=True)}')
            ty = NUM(0, min(b.const - 1, a.ty.hi))
            return self.wire(ty, f'{self.as_num(a, w)} % {self.as_num(b, w)}')
        if o in ('<<', '>>'):
            if b.const is None:
                if o == '<<' and a.const is not None and a.const >= 0 and b.ty.lo >= 0:
                    ty = NUM(a.const << b.ty.lo, a.const << b.ty.hi)
                    sh = f'{b.v}' if b.ty.kind != 'num' else f'{b.v}[{max(1, b.ty.hi.bit_length()) - 1}:0]'
                    return self.wire(ty, f'{self.as_num(a, ty.nbits)} <<< {sh}')
                raise FcpTypeError(f'shift amount must be constant in {unparse(n)}')
            k = b.const
            if a.const is not None:
                return self.const(a.const << k if o == '<<' else a.const >> k)
            if a.ty.kind == 'bits':
                return self.wire(a.ty, f'{a.v} {o} {k}')
            ty = NUM(a.ty.lo << k, a.ty.hi << k) if o == '<<' else NUM(a.ty.lo >> k, a.ty.hi >> k)
            if o == '<<':
                return self.wire(ty, f'{self.as_num(a, ty.nbits)} <<< {k}')
            return self.wire(ty, f'{a.v} >>> {k}')
        raise AssertionError(o)

    # -- functions, including the past-time temporal operators -----------------
    def _defined(self, a: Val, n: Node, sc: Scope, default: bool) -> str:
        """Operand of a history operator.  An operand that looks back d cycles
        is undefined in the first d cycles after a reset (its prev() would read
        the reset cycle); the operator skips those cycles, as if the operand were
        `default` there.  `_seg` is the monitor's cycles-since-reset counter."""
        d = lookback(n, sc.syms)
        if not d:
            return a.v
        return f'((_seg < {d}) || {a.v})' if default else f'((_seg >= {d}) && {a.v})'

    def prev_of(self, x: Val, depth: int = 1) -> Val:
        if x.const is not None:
            return x
        if isinstance(x, SeqVal):
            d = self.prev_of(Val(x.v, x.ty), depth)
            return SeqVal(d.v, x.ty, ln=self.prev_of(x.ln, depth))
        cur = x
        for _ in range(depth):
            r = self.reg(cur.ty, self.fresh('_p'), comment=f'prev({cur.v})')
            self.seq.append(f'    {r} <= {cur.v};')
            cur = Val(r, x.ty)
        return cur

    def _call(self, n: Node, sc: Scope) -> Val:
        f, args = n.val, n.args
        if f not in FUNCS:
            raise FcpTypeError(f'unknown function {f!r} (available: {", ".join(sorted(FUNCS))})')

        def arity(k):
            if len(args) not in (k if isinstance(k, tuple) else (k,)):
                raise FcpTypeError(f'{f}() takes {k} argument(s), got {len(args)} in {unparse(n)}')

        if f == 'prev':
            arity((1, 2))
            depth = 1
            if len(args) == 2:
                d = self.compile(args[1], sc)
                if d.const is None or d.const < 1:
                    raise FcpTypeError(f'prev depth must be a constant >= 1 in {unparse(n)}')
                depth = d.const
            self.max_prev = max(self.max_prev, depth)
            return self.prev_of(self.compile(args[0], sc), depth)
        if f in ('rose', 'fell'):
            arity(1)
            a = self.boolean(args[0], sc, f'argument of {f}')
            p = self.prev_of(a)
            self.max_prev = max(self.max_prev, 1)
            return self.wire(BOOL, f'{a.v} && !{p.v}' if f == 'rose' else f'!{a.v} && {p.v}')
        if f in ('stable', 'changed'):
            arity(1)
            a = self.compile(args[0], sc)
            p = self.prev_of(a)
            self.max_prev = max(self.max_prev, 1)
            if isinstance(a, SeqVal):
                eq = self.seq_eq(a, p)
                return eq if f == 'stable' else self.notv(eq)
            if a.const is not None:
                return self.const(1 if f == 'stable' else 0, BOOL)
            return self.wire(BOOL, f'{a.v} {"==" if f == "stable" else "!="} {p.v}')
        if f in ('once', 'hist'):
            arity(1)
            a = self.boolean(args[0], sc, f'argument of {f}')
            r = self.reg(BOOL, self.fresh('_o' if f == 'once' else '_h'), init=0 if f == 'once' else 1)
            if f == 'once':
                v = self.wire(BOOL, f'{r} || {self._defined(a, args[0], sc, False)}')
                self.seq.append(f'    {r} <= {self.rst} ? 1\'b0 : {v.v};')
            else:
                v = self.wire(BOOL, f'{r} && {self._defined(a, args[0], sc, True)}')
                self.seq.append(f'    {r} <= {self.rst} ? 1\'b1 : {v.v};')
            return v
        if f == 'since':
            arity(2)
            a = self.boolean(args[0], sc, 'first argument of since')
            b = self.boolean(args[1], sc, 'second argument of since')
            r = self.reg(BOOL, self.fresh('_s'), init=0)
            v = self.wire(BOOL, f'{self._defined(b, args[1], sc, False)} || '
                                f'({self._defined(a, args[0], sc, True)} && {r})')
            self.seq.append(f'    {r} <= {self.rst} ? 1\'b0 : {v.v};')
            return v
        if f == 'len':
            arity(1)
            a = self.compile(args[0], sc)
            if not isinstance(a, SeqVal):
                raise FcpTypeError(f'len() needs a string or a list in {unparse(n)}')
            return a.ln
        if f in CHARS:
            arity(1)
            c = self.num(args[0], sc)
            return self.orv([self.andv([self.cmpv(c, self.const(lo), '>='), self.cmpv(c, self.const(hi), '<=')])
                             for lo, hi in CHARS[f]])
        if f in ('lower', 'upper'):
            arity(1)
            c = self.num(args[0], sc)
            lo, hi, d = (65, 90, 32) if f == 'lower' else (97, 122, -32)
            inr = self.andv([self.cmpv(c, self.const(lo), '>='), self.cmpv(c, self.const(hi), '<=')])
            return self.ite_num(inr, self.addv([c, self.const(d)]), c)
        if f in ('onehot', 'onehot0', 'countones', 'any', 'all'):
            arity(1)
            a = self.num(args[0], sc)
            if a.ty.kind == 'num':
                raise FcpTypeError(f'{f}() needs a bit-vector argument in {unparse(n)}')
            w = a.ty.nbits
            if f == 'any':
                return self.wire(BOOL, f'|{a.v}')
            if f == 'all':
                return self.wire(BOOL, f'&{a.v}')
            if f == 'countones':
                ty = NUM(0, w)
                terms = ' + '.join(f"{{{ty.nbits - 1}'b0, {a.v}[{i}]}}" if w > 1 else f"{{{ty.nbits - 1}'b0, {a.v}}}"
                                   for i in range(w))
                return self.wire(ty, f'$signed({terms})')
            if w == 1:
                return self.wire(BOOL, '1\'b1' if f == 'onehot0' else a.v)
            m1 = self.wire(BITS(w), f"{a.v} - {vconst(1, BITS(w))}")
            z = self.wire(BOOL, f"({a.v} & {m1.v}) == {vconst(0, BITS(w))}")
            return z if f == 'onehot0' else self.wire(BOOL, f'{z.v} && (|{a.v})')
        if f in ('min', 'max'):
            arity(2)
            a, b = self.num(args[0], sc), self.num(args[1], sc)
            if f == 'min':
                ty = NUM(min(a.ty.lo, b.ty.lo), min(a.ty.hi, b.ty.hi))
            else:
                ty = NUM(max(a.ty.lo, b.ty.lo), max(a.ty.hi, b.ty.hi))
            w = max(signed_bits(a.ty.lo, a.ty.hi), signed_bits(b.ty.lo, b.ty.hi), ty.nbits)
            cmp = '<' if f == 'min' else '>'
            hull = NUM(min(a.ty.lo, b.ty.lo), max(a.ty.hi, b.ty.hi))
            raw = self.wire(hull, f'({self.as_num(a, w)} {cmp} {self.as_num(b, w)}) ? {self.as_num(a, w)} : '
                                  f'{self.as_num(b, w)}')
            # the smaller (larger) of the two lies in ty, which can be far narrower than the
            # hull: min(n, 28) is at most 28, so 1 << min(n, 28) needs 30 bits, not 65,537
            if ty.nbits == hull.nbits:
                return Val(raw.v, ty)
            return self.wire(ty, self.as_num(raw, ty.nbits, trunc=True))
        if f == 'zext':
            arity(2)
            a, wv = self.num(args[0], sc), self.num(args[1], sc)
            if wv.const is None:
                raise FcpTypeError('zext width must be constant')
            return self.wire(BITS(wv.const), self.as_bits(a, wv.const))
        raise AssertionError(f)


def depends_on(n: Node, scope: Scope, kinds: set[str], seen=None) -> set[str]:
    """Names of the given symbol kinds that n depends on (through defs)."""
    seen = seen if seen is not None else set()
    out = set()
    for r in refs(n):
        if r in seen:
            continue
        seen.add(r)
        s = scope.syms.get(r)
        if s is None:
            continue
        if s.kind in kinds:
            out.add(r)
        if s.kind == 'def' and s.node is not None:
            out |= depends_on(s.node, scope, kinds, seen)
    return out
