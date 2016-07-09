import ast

class Var(ast.AST):
    _fields = ["id", "type"]

    def __init__(self, id, type=None):
        self.id = id
        self.type = type

class Assign(ast.AST):
    _fields = ["ref", "val", "type"]

    def __init__(self, ref, val, type=None):
        self.ref = ref
        self.val = val
        self.type = type

class Return(ast.AST):
    _fields = ["val"]

    def __init__(self, val):
        self.val = val

class Loop(ast.AST):
    _fields = ["var", "begin", "end", "body"]

    def __init__(self, var, begin, end, body):
        self.var = var
        self.begin = begin
        self.end = end
        self.body = body

class App(ast.AST):
    _fields = ["fn", "args"]

    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

class Fun(ast.AST):
    _fields = ["fname", "args", "body"]

    def __init__(self, fname, args, body):
        self.fname = fname
        self.args = args
        self.body = body

class LitInt(ast.AST):
    _fields = ["n"]

    def __init__(self, n, type=None):
        self.n = n
        self.type = type

class LitFloat(ast.AST):
    _fields = ["n"]

    def __init__(self, n, type=None):
        self.n = n
        self.type = None

class LitBool(ast.AST):
    _fields = ["n"]

    def __init__(self, n):
        self.n = n

class Prim(ast.AST):
    _fields = ["fn", "args"]

    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

class Index(ast.AST):
    _fields = ["val", "ix"]

    def __init__(self, val, ix):
        self.val = val
        self.ix = ix

class Noop(ast.AST):
    _fields = []

primops = {ast.Add: "add#", ast.Mult: "mult#"}