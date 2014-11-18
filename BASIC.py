#!/bin/env python
# coding: utf-8

"""
BASIC.py

A BASIC interpreter, guessed-engineered from manual:
  http://www.dartmouth.edu/basicfifty/basicmanual_1964.pdf

by @alejolp at:
  https://github.com/alejolp/BASIC

"""

import sys
import string 

class BasicSyntaxError(Exception):
    pass

TOK_WS = " \t"
TOK_OPS = "()+-*/^"
TOK_VAR = string.ascii_letters #aA
TOK_NUM = string.digits

TOK_TYPE_OP = 0
TOK_TYPE_VAR = 1
TOK_TYPE_NUM = 2
TOK_TYPE_STR = 3
TOK_TYPE_END = 9

def debug(*args):
    #print(*args)
    pass

def tok_expr(S):
    """
    Tokenizer for general expressions:
     - Arithmetic expressions: (1+1) + 2 * (3^2)
     - String literals: "Hello, World"
    """
    i = 0
    T = []
    while i < len(S):
        while i < len(S) and S[i] in TOK_WS:
            i = i + 1

        if i == len(S):
            break

        if S[i] in TOK_OPS:
            T.append((TOK_TYPE_OP, S[i]))
            i = i + 1
        elif S[i] in TOK_VAR:
            T.append((TOK_TYPE_VAR, S[i]))
            i = i + 1
        elif S[i] in TOK_NUM or S[i] == '.':
            start = i
            while i < len(S) and S[i] in TOK_NUM:
                i = i + 1
            if i < len(S) and S[i] == '.':
                i = i + 1
                while i < len(S) and S[i] in TOK_NUM:
                    i = i + 1
            if i < len(S) and S[i] in "eE":
                i = i + 1
                if i < len(S) and S[i] == '-': #1e-1
                    i = i + 1
                while i < len(S) and S[i] in TOK_NUM:
                    i = i + 1
            T.append((TOK_TYPE_NUM, S[start:i]))
        elif S[i] == '"':
            start = i
            while i < len(S) and S[i] != '"':
                i = i + 1
            if S[i] != '"':
                raise BasicSyntaxError("Incomplete string")
            i = i + 1
            T.append((TOK_TYPE_STR, S[start:i]))
        else:
            raise BasicSyntaxError("Unknown token")
    T.append((TOK_TYPE_END, None))
    return T

class parser:
    def __init__(self, toks):
        self.toks = toks
        self.pos  = 0

    def tok_peek(self):
        assert self.pos >= 0 and self.pos < len(self.toks)
        return self.toks[self.pos]

    def tok_next(self):
        t = self.tok_peek()
        debug("Eat: ", t)
        self.pos = self.pos + 1
        return t

    def tok_match_type(self, t):
        if not self.tok_peek()[0] == t:
            raise BasicSyntaxError("missing symbol type " + repr(t))
        return self.tok_next()

    def tok_match_lit(self, t):
        """
        match literal token
        """
        if not self.tok_peek()[1] == t:
            raise BasicSyntaxError("missing symbol: " + repr(t))
        return self.tok_next()

    def parse(self):
        """
        expr --> term { + term }
        term --> factor { * factor }
        factor --> -( expr ) | ( expr ) | signed-number
        signed-number --> - power | power
        power --> number { ^ number }
        """
        debug("parse")
        node = ['root', ]
        node.append(self.parse_expr())
        node.append(self.tok_match_type(TOK_TYPE_END))
        return node

    def parse_expr(self):
        debug("parse_expr")
        node = ['expr', ]

        node.append(self.parse_term())
        while self.tok_peek()[1] in ['+', '-']:
            node.append(self.tok_next())
            node.append(self.parse_term())
        return node

    def parse_term(self):
        debug("parse_term")
        node = ['term', ]

        node.append(self.parse_factor())
        while self.tok_peek()[1] in ['*', '/']:
            node.append(self.tok_next())
            node.append(self.parse_factor())

        return node

    def parse_factor(self):
        debug("parse_factor")
        node = ['factor', ]
        if self.tok_peek()[1] in ['(']: # '-'
            #if self.tok_peek()[1] == '-':
            #    node.append(self.tok_next())
            node.append(self.tok_match_lit('('))
            node.append(self.parse_expr())
            node.append(self.tok_match_lit(')'))
        else:
            node.append(self.parse_signed_number())
        return node

    def parse_signed_number(self):
        debug("parse_signed_number")
        node = ['signed_number', ]
        if self.tok_peek()[1] == '-':
            node.append(self.tok_next())
        node.append(self.parse_power())
        return node

    def parse_power(self):
        debug("parse_power")
        node = ['power', ]
        node.append(self.tok_match_type(TOK_TYPE_NUM))
        if self.tok_peek()[1] == '^':
            node.append(self.tok_next())
            node.append(self.tok_match_type(TOK_TYPE_NUM))
        return node

class evaluator:
    def __init__(self):
        pass

    def eval_node_leaf(self, leaf):
        return float(leaf)

    def eval_node(self, node):
        # print("QQQ", node)
        if node[0] == 'root':
            return self.eval_node(node[1])
        elif node[0] == 'expr':
            left = self.eval_node(node[1])
            i = 2
            while i < len(node):
                right = self.eval_node(node[i + 1])
                if node[i][1] == '+':
                    left = left + right
                elif node[i][1] == '-':
                    left = left - right
                else:
                    assert False
                i = i + 2
            return left
        elif node[0] == 'term':
            left = self.eval_node(node[1])
            i = 2
            while i < len(node):
                right = self.eval_node(node[i + 1])
                if node[i][1] == '*':
                    left = left * right
                elif node[i][1] == '/':
                    left = left / right
                else:
                    assert False
                i = i + 2
            return left
        elif node[0] == 'factor':
            if node[1][1] == '-':
                return -1 * self.eval_node(node[3])
            if node[1][1] == '(':
                return self.eval_node(node[2])
            return self.eval_node(node[1])
        elif node[0] == 'signed_number':
            if node[1][1] == '-':
                return -1 * self.eval_node(node[2])
            return self.eval_node(node[1])
        elif node[0] == 'power':
            if len(node) == 4:
                return self.eval_node_leaf(node[1][1]) ** self.eval_node_leaf(node[3][1])
            return self.eval_node_leaf(node[1][1])
        assert False

def parse_expr(S):
    toks = tok_expr(S)
    print("toks", toks)
    p = parser(toks)
    root = p.parse()
    print(root)
    return root

def parse_full_line(line):
    parts = line.split(None, 1)

    # Allow empty lines
    if len(parts) == 0:
        return None

    op = parts[0].upper()

    if op == 'END':
        if len(parts) != 1:
            raise BasicSyntaxError()
        return ('END', )

    if op == 'PRINT':
        if len(parts) == 1:
            raise BasicSyntaxError()
        node = parse_expr(parts[1])
        return ('PRINT', node, eval_node(node))

    if op == 'LET':
        if len(parts) <= 3:
            raise BasicSyntaxError()
        return ('LET', )

    if op == 'FOR':
        return ('FOR', )

    if op == 'NEXT':
        return ('NEXT', )

    if op == 'GO':
        return ('GOTO', )

    if op == 'GOTO':
        return ('GOTO', )

    if op == 'IF':
        return ('IF', )

    if op == 'DEF':
        return ('DEF', )

    if op == 'READ':
        return ('READ', )

    if op == 'DATA':
        return ('DATA', )

def main():
    if len(sys.argv) <= 1:
        print("Usage: BASIC.py file.bas")
        return

    # List of parsed lines
    L = [None] * 100000

    # Allow to print all the errors in the file
    errors = False

    with open(sys.argv[1], "r") as f:
        for line in f:
            # Remove whitespace at the end
            line = line.rstrip()

            # Allow blank lines
            if len(line) == 0:
                continue

            # Get line number
            try:
                line_num, line_rest = line.split(None, 1)
                line_num = int(line_num)
            except ValueError:
                print("Invalid syntax: " + line)
                errors = True
                continue

            if (line_num <= 0) or (line_num > 99999):
                print("Line number out of range 1..99999")
                errors = True
                continue

            # Parse the rest
            try:
                L[line_num] = parse_full_line(line_rest)
                print(L[line_num])

            except BasicSyntaxError as ex:
                print("Invalid syntax: " + str(ex))
                print("At line: " + line)
                errors = True
                continue

if __name__ == '__main__':
    main()
