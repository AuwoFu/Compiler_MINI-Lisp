import math
import operator as op

## type


Symbol = str  # A Scheme Symbol is implemented as a Python str
Number = (int, float)  # A Scheme Number is implemented as a Python int or float
List = list  # A Scheme List is implemented as a Python list
Boolean = bool


## parser
def parse(program: str):
    # read input & start parse
    return read_from_tokens(tokenize(program))


def tokenize(chars: str) -> list:
    # change input characters into tokens
    return chars.replace('(', ' ( ').replace(')', ' ) ').split()


pr = 0


def read_from_tokens(tokens: list):
    # check token list
    global pr
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF')
    token = tokens.pop(0)
    # mini-lips's command :(operator arg arg)
    # make sure each element is truly being a complete sentence that we want
    if token == '(':
        cmd = []
        pr += 1
        while pr != 0:
            if tokens[0] != ')':
                cmd.append(read_from_tokens(tokens))
            else:
                pr -= 1
                tokens.pop(0)
                return cmd
        return cmd
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        return atom(token)


def atom(token: str):
    # classify number & symbol
    try:
        return int(token)
    except ValueError:
        return Symbol(token)


## Enviornment (with token define)
def standard_env():
    "An environment with some Scheme standard procedures."
    env = Env()
    env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update({
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
        '>': op.gt, '<': op.lt, '=': op.eq,
        'mod': op.mod,
        'and': op.and_,
        'or': op.or_,
        'not': op.not_,

        '#t': True,
        '#f': False,
        'print-num': lambda exp: print(eval(exp, env)),
        'print-bool': lambda exp: print('#t') if eval(exp, env) else print('#f'),
    })
    return env


class Env(dict):
    # An environment: a dict of {'var':val} pairs, with an outer Env.
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        "Find the innermost Env where var appears."
        return self if (var in self) else self.outer.find(var)


## Procedures (Function)
class Procedure(object):
    "A user-defined Scheme procedure."

    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
        for line in self.body:
            if type(line) == list and line[0] == 'define':
                eval(line, self.env)

    def __call__(self, *args):
        for line in self.body:
            if type(line) != list or (type(line) == list and line[0] != 'define'):
                result = eval(line, Env(self.parms, args, self.env))
        return result
        # return result=eval(self.body, Env(self.parms, args, self.env))


global_env = standard_env()


## evalution
def eval(x, env=global_env):
    # evaluation expression
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif isinstance(x, Boolean):
        return x
    elif not isinstance(x, List):  # constant literal
        return x
    elif x[0] == 'if':  # (if test conseq alt)
        if len(x) < 4:
            Error()
        (_, test, conseq, alt) = x
        typeCheck('logical', eval(test, env))
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'define':  # (define var exp)
        if len(x) < 3:
            Error()
        (_, name, exp) = x
        env[name] = eval(exp, env)
    elif x[0] == 'fun' or x[0] == 'lambda':  # (fun (var...) body)
        if len(x) < 3:
            Error()
        body = []
        for k in range(2, len(x)):
            body.append(x[k])
        return Procedure(x[1], body, env)
    elif x[0] == '+':  # (+ EXP EXP+)
        if len(x) < 3:
            Error()
        add_sum = 0
        for k in range(1, len(x)):
            exp = x[k]
            result = eval(exp, env)
            if typeCheck('math', result):
                add_sum += int(result)
        return add_sum
    elif x[0] == '-':  # (- EXP) or (- EXP EXP)
        if len(x) < 2:
            Error()
        if len(x) == 2:
            (_, exp) = x
            typeCheck('math', eval(exp, env))
            return -1 * (eval(exp, env))
        else:
            (_, exp1, exp2) = x
            typeCheck('math', eval(exp1, env))
            typeCheck('math', eval(exp2, env))
            return (eval(exp1, env)) - (eval(exp2, env))
    elif x[0] == '*':  # (* EXP EXP+)
        if len(x) < 2:
            Error()
        multi_sum = 1
        for k in range(1, len(x)):
            exp = x[k]
            result = eval(exp, env)
            if typeCheck('math', result):
                multi_sum *= int(result)
        return int(multi_sum)
    elif x[0] == 'mod' or x[0] == '/' or x[0] == '>' or x[
        0] == '<':  # (mod EXP EXP) or (/ EXP EXP) or  (> EXP EXP) or (< EXP EXP)
        if len(x) < 3:
            Error()
        (_, exp1, exp2) = x
        typeCheck('math', eval(exp1, env))
        typeCheck('math', eval(exp2, env))
        if x[0] == 'mod':
            return int((eval(exp1, env)) % (eval(exp2, env)))
        elif x[0] == '/':
            return int((eval(exp1, env)) / (eval(exp2, env)))
        elif x[0] == '>':
            return op.gt(eval(exp1, env), eval(exp2, env))
        else:
            return op.lt(eval(exp1, env), eval(exp2, env))
    elif x[0] == '=':  # (= EXP EXP+)
        if len(x) < 3:
            Error()
        bool_result = True
        first = eval(x[1], env)
        typeCheck('math', first)
        for k in range(2, len(x)):
            exp = x[k]
            result = eval(exp, env)
            if typeCheck('math', result):
                if first != result:
                    bool_result = False
        return bool_result
    elif x[0] == 'and':  # (and EXP EXP+)
        if len(x) < 3:
            Error()
        bool_result = True
        for k in range(1, len(x)):
            exp = x[k]
            result = eval(exp, env)
            if typeCheck('logical', result):
                if not result:
                    bool_result = False
        return bool_result
    elif x[0] == 'or':  # (or EXP EXP+)
        if len(x) < 3:
            Error()
        bool_result = False
        for k in range(1, len(x)):
            exp = x[k]
            result = eval(exp, env)
            if typeCheck('logical', result):
                if result:
                    bool_result = True
        return bool_result
    elif x[0] == 'not':  # (not EXP)
        if len(x) < 2:
            Error()
        (_, exp) = x
        typeCheck('logical', eval(exp, env))
        return not eval(exp, env)
    else:  # (proc arg...)
        proc = eval(x[0], env)
        args = [eval(exp, env) for exp in x[1:]]
        return proc(*args)


# check all args are legal
def typeCheck(cmd_type: str, x):
    if cmd_type == 'logical':
        if type(x) == bool:
            return True
    elif cmd_type == 'math':
        if type(x) == int or type(x) == float:
            return True
    print("Type Error")
    exit(0)


# input format is illegal
def Error():
    print('Syntax Error')
    exit(0)


## main
file_path="../testcase/test.lsp"

if __name__ == '__main__':
    while True:
        file_path = input()
        file_path = "../0107/" + file_path+"_hidden.lsp"
        f = open(file_path, mode="r") # read from txt text
        # f = open(file_path, mode="r", encoding="utf-8") # text copy from pdf
        text = []
        line = f.read()
        r = 0  # RPR number
        l = 0  # LPR number
        start = 0
        for i in range(len(line)):
            if line[i] == '(':
                if r == 0:
                    start = i
                r += 1
            elif line[i] == ')':
                l += 1

            if r == l and r != 0:
                buf = line[start:i + 1]
                start = i + 1
                text.append(buf)
                l = 0
                r = 0
        if r != l:
            Error()

        tokens = []
        for cmd in text:
            tokens.append(parse(cmd))
        # print(tokens)
        for tree in tokens:
            eval(tree)
