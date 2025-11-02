import sys, re



# Lexer
TOKEN_RE = re.compile(r'\s*(?:(\d+)|([A-Za-z_]\w*)|(==|!=|<=|>=)|(.))')

def tokenize(src):
    lines = []
    for line in src.splitlines():
        line = line.split('#', 1)[0].rstrip()
        if line:
            lines.append(line)
    tokens = []
    indent_stack = [0]
    for line in lines:
        # Calculate indent (spaces or tabs, tab=4 spaces)
        indent = 0
        for c in line:
            if c == ' ':
                indent += 1
            elif c == '\t':
                indent += 4
            else:
                break
        line = line.lstrip()
        if not line:
            continue
        # Handle dedent
        while indent < indent_stack[-1]:
            tokens.append(('DEDENT', None))
            indent_stack.pop()
        # Handle indent
        if indent > indent_stack[-1]:
            tokens.append(('INDENT', None))
            indent_stack.append(indent)
        # Tokenize the line
        pos = 0
        while pos < len(line):
            m = TOKEN_RE.match(line, pos)
            if not m:
                raise SyntaxError(f'Illegal character at {pos} in {line}')
            num, ident, cmpop, other = m.groups()
            pos = m.end()
            if num:
                tokens.append(('NUMBER', int(num)))
            elif ident:
                tokens.append(('IDENT', ident))
            elif cmpop:
                tokens.append(('OP', cmpop))
            else:
                c = other
                if c in '+-*/%=<>!':
                    tokens.append(('OP', c))
                elif c in '(){},:':
                    tokens.append((c, c))
                else:
                    raise SyntaxError(f'Unknown token {c}')
    # Close all indents
    while len(indent_stack) > 1:
        tokens.append(('DEDENT', None))
        indent_stack.pop()
    tokens.append(('EOF', None))
    return tokens

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def peek_n(self, n):
        # safe lookahead: return token at i+n or ('EOF', None)
        idx = self.i + n
        if idx < len(self.tokens):
            return self.tokens[idx]
        return ('EOF', None)

    def next(self):
        t = self.tokens[self.i]; self.i += 1; return t

    def accept(self, typ, val=None):
        t = self.peek()
        if t[0] == typ and (val is None or t[1] == val):
            return self.next()
        return None

    def expect(self, typ, val=None):
        t = self.next()
        if t[0] != typ or (val is not None and t[1] != val):
            raise SyntaxError(f'Expected {typ} {val}, got {t}')
        return t

    def parse(self):
        stmts = []
        while self.peek()[0] != 'EOF':
            stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        t = self.peek()
        if t[0] == 'IDENT' and t[1] in ('let', 'var', 'const', 'set'):
            self.next()
            name = self.expect('IDENT')[1]
            # accept: let x = 10  OR let x be 10  OR let x is 10 (or let x is equal to 10)
            if self.accept('OP', '='):
                pass
            elif self.accept('IDENT', 'be'):
                pass
            elif self.accept('IDENT', 'is'):
                # optionally skip 'equal' 'to'
                self.accept('IDENT', 'equal')
                self.accept('IDENT', 'to')
            else:
                raise SyntaxError('Expected = or be after let name')
            expr = self.parse_expr()
            return ('let', name, expr)
        if t[0] == 'IDENT' and t[1] == 'print':
            self.next()
            expr = self.parse_expr()
            return ('print', expr)
        if t[0] == 'IDENT' and t[1] == 'if':
            self.next()
            cond = self.parse_expr()
            self.expect(':', ':')
            body = self.parse_block()
            return ('if', cond, body)
        if t[0] == 'IDENT' and t[1] == 'while':
            self.next()
            cond = self.parse_expr()
            self.expect(':', ':')
            body = self.parse_block()
            return ('while', cond, body)
        # assignment or expression
        if t[0] == 'IDENT':
            # lookahead for '='
            # allow forms: x = 1   OR  x is 1  OR x be 1
            nxt = self.peek_n(1)
            if nxt[0] == 'OP' and nxt[1] == '=':
                name = self.next()[1]
                self.next()  # =
                expr = self.parse_expr()
                return ('assign', name, expr)
            if nxt[0] == 'IDENT' and nxt[1] in ('be','is'):
                # ensure this is not a comparator phrase like 'is greater than'
                third = self.peek_n(2)
                if not (third[0] == 'IDENT' and third[1] in ('greater','less','not','equal')):
                    name = self.next()[1]
                    # consume 'be' or 'is'
                    self.next()
                    # optionally skip 'equal' 'to' after 'is'
                    if self.peek()[0] == 'IDENT' and self.peek()[1] == 'equal':
                        self.next()
                    if self.peek()[0] == 'IDENT' and self.peek()[1] == 'to':
                        self.next()
                    expr = self.parse_expr()
                    return ('assign', name, expr)
        expr = self.parse_expr()
        return ('expr', expr)

    def parse_block(self):
        self.expect('INDENT', None)
        stmts = []
        while self.peek()[0] != 'DEDENT' and self.peek()[0] != 'EOF':
            stmts.append(self.parse_stmt())
        self.expect('DEDENT', None)
        return stmts

    # Expression parsing (precedence climbing)
    def parse_expr(self):
        return self.parse_cmp()

    def parse_cmp(self):
        node = self.parse_add()
        while True:
            # symbol operators (==, !=, <=, >=, <, >)
            if self.peek()[0] == 'OP' and self.peek()[1] in ('==','!=','<','>','<=','>='):
                op = self.next()[1]
                right = self.parse_add()
                node = (op, node, right)
                continue
            # boolean operators: and, or, not
            if self.peek()[0] == 'IDENT' and self.peek()[1] in ('and', 'or'):
                op = self.next()[1]
                right = self.parse_add()
                node = (op, node, right)
                continue
            # English-like comparison phrases, e.g. 'is equal to', 'is not equal to',
            # 'is greater than', 'is less than or equal to'
            t = self.peek()
            if t[0] == 'IDENT' and t[1] == 'is':
                # look for patterns after 'is'
                a = self.peek_n(1)
                b = self.peek_n(2)
                c = self.peek_n(3)
                # is not equal to
                if a[0] == 'IDENT' and a[1] == 'not' and b[0] == 'IDENT' and b[1] == 'equal':
                    # consume 'is' 'not' 'equal' [to]
                    self.next(); self.next(); self.next()
                    self.accept('IDENT','to')
                    right = self.parse_add()
                    node = ('!=', node, right)
                    continue
                # is equal to / is equal
                if a[0] == 'IDENT' and a[1] == 'equal':
                    self.next(); self.next()
                    self.accept('IDENT','to')
                    right = self.parse_add()
                    node = ('==', node, right)
                    continue
                # is greater than [or equal to]
                if a[0] == 'IDENT' and a[1] == 'greater' and b[0] == 'IDENT' and b[1] == 'than':
                    # consume 'is' 'greater' 'than'
                    self.next(); self.next(); self.next()
                    # optional 'or equal to' or 'or equal'
                    if self.peek()[0] == 'IDENT' and self.peek()[1] == 'or':
                        self.next()
                        self.accept('IDENT','equal')
                        self.accept('IDENT','to')
                        right = self.parse_add()
                        node = ('>=', node, right)
                        continue
                    right = self.parse_add()
                    node = ('>', node, right)
                    continue
                # is less than [or equal to]
                if a[0] == 'IDENT' and a[1] == 'less' and b[0] == 'IDENT' and b[1] == 'than':
                    self.next(); self.next(); self.next()
                    if self.peek()[0] == 'IDENT' and self.peek()[1] == 'or':
                        self.next()
                        self.accept('IDENT','equal')
                        self.accept('IDENT','to')
                        right = self.parse_add()
                        node = ('<=', node, right)
                        continue
                    right = self.parse_add()
                    node = ('<', node, right)
                    continue
            # also allow single-word 'equals' and 'not' forms
            if t[0] == 'IDENT' and t[1] in ('equals','equal'):
                self.next()
                self.accept('IDENT','to')
                right = self.parse_add()
                node = ('==', node, right)
                continue
            if t[0] == 'IDENT' and t[1] == 'not':
                # 'not equal to' or 'not equal'
                a = self.peek_n(1)
                if a[0] == 'IDENT' and a[1] == 'equal':
                    self.next(); self.next()
                    self.accept('IDENT','to')
                    right = self.parse_add()
                    node = ('!=', node, right)
                    continue
            break
        return node

    def parse_add(self):
        node = self.parse_mul()
        while True:
            t = self.peek()
            if t[0] == 'OP' and t[1] in ('+','-'):
                op = self.next()[1]
                right = self.parse_mul()
                node = (op, node, right)
            else:
                break
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while True:
            t = self.peek()
            if t[0] == 'OP' and t[1] in ('*','/'):
                op = self.next()[1]
                right = self.parse_unary()
                node = (op, node, right)
            else:
                break
        return node

    def parse_unary(self):
        t = self.peek()
        if t[0] == 'OP' and t[1] == '-':
            self.next()
            return ('neg', self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()
        if t[0] == 'NUMBER':
            self.next()
            return ('num', t[1])
        if t[0] == 'IDENT':
            self.next()
            return ('var', t[1])
        if t[0] == '(':
            self.next()
            node = self.parse_expr()
            self.expect(')', ')')
            return node
        raise SyntaxError(f'Unexpected token {t}')

# Evaluator
class Interpreter:
    def __init__(self):
        self.env = {}

    def eval(self, node):
        kind = node[0]
        if kind == 'num': return node[1]
        if kind == 'var':
            name = node[1]
            if name in self.env: return self.env[name]
            raise NameError(f'Undefined variable {name}')
        if kind == 'neg': return -self.eval(node[1])
        if kind in ('+','-','*','/','%'):
            a = self.eval(node[1]); b = self.eval(node[2])
            if kind == '+': return a + b
            if kind == '-': return a - b
            if kind == '*': return a * b
            if kind == '/': return a // b if b != 0 else (_raise(ZeroDivisionError('division by zero')))
            if kind == '%': return a % b if b != 0 else (_raise(ZeroDivisionError('modulo by zero')))
        if kind in ('==','!=','<','>','<=','>='):
            a = self.eval(node[1]); b = self.eval(node[2])
            if kind == '==': return 1 if a == b else 0
            if kind == '!=': return 1 if a != b else 0
            if kind == '<': return 1 if a < b else 0
            if kind == '>': return 1 if a > b else 0
            if kind == '<=': return 1 if a <= b else 0
            if kind == '>=': return 1 if a >= b else 0
        if kind == 'and':
            a = self.eval(node[1]); b = self.eval(node[2])
            return 1 if a and b else 0
        if kind == 'or':
            a = self.eval(node[1]); b = self.eval(node[2])
            return 1 if a or b else 0
        raise RuntimeError(f'Unknown expr {node}')

    def exec_stmt(self, stmt):
        typ = stmt[0]
        if typ == 'let':
            _, name, expr = stmt
            self.env[name] = self.eval(expr)
        elif typ == 'assign':
            _, name, expr = stmt
            if name not in self.env:
                # allow implicit creation
                self.env[name] = self.eval(expr)
            else:
                self.env[name] = self.eval(expr)
        elif typ == 'print':
            val = self.eval(stmt[1])
            print(val)
        elif typ == 'if':
            cond = self.eval(stmt[1])
            if cond:
                self.exec_block(stmt[2])
        elif typ == 'while':
            while self.eval(stmt[1]):
                self.exec_block(stmt[2])
        elif typ == 'expr':
            self.eval(stmt[1])
        else:
            raise RuntimeError(f'Unknown stmt {stmt}')

    def exec_block(self, stmts):
        for s in stmts:
            self.exec_stmt(s)

def _raise(ex):
    raise ex

def run(src):
    tokens = tokenize(src)
    parser = Parser(tokens)
    program = parser.parse()
    interp = Interpreter()
    for s in program:
        interp.exec_stmt(s)

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 test.py <source.tl>')
        print('Runs included sample program...')
        src = '''
# sample: factorial of 5
let n = 5
let fact = 1
while n > 1:
  fact = fact * n
  n = n - 1
print fact
'''
        run(src)
        return
    with open(sys.argv[1], 'r') as f:
        run(f.read())

if __name__ == '__main__':
    main()

