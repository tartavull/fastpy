import ast

class Var(ast.AST):
    """Variable
    
    Attributes:
        id (TYPE): Description
        type (TYPE): Description
    """
    _fields = ["id", "type"]

    def __init__(self, id, type=None):
        self.id = id
        self.type = type

class Assign(ast.AST):
    """Assignment
    
    Attributes:
        ref (TYPE): Description
        type (TYPE): Description
        val (TYPE): Description
    """
    _fields = ["ref", "val", "type"]

    def __init__(self, ref, val, type=None):
        self.ref = ref
        self.val = val
        self.type = type

class Return(ast.AST):
    """Return
    
    Attributes:
        val (TYPE): Description
    """
    _fields = ["val"]

    def __init__(self, val):
        self.val = val

class Loop(ast.AST):
    """Loop Construct
    
    Attributes:
        begin (TYPE): Description
        body (TYPE): Description
        end (TYPE): Description
        var (TYPE): Description
    """
    _fields = ["var", "begin", "end", "body"]

    def __init__(self, var, begin, end, body):
        self.var = var
        self.begin = begin
        self.end = end
        self.body = body

class App(ast.AST):
    """Variadic Application
    
    Attributes:
        args (TYPE): Description
        fn (TYPE): Description
    """
    _fields = ["fn", "args"]

    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

class Fun(ast.AST):
    """Variadic Function
    
    Attributes:
        args (TYPE): Description
        body (TYPE): Description
        fname (TYPE): Description
    """
    _fields = ["fname", "args", "body"]

    def __init__(self, fname, args, body):
        self.fname = fname
        self.args = args
        self.body = body

class LitInt(ast.AST):
    """Integer
    
    Attributes:
        n (TYPE): Description
        type (TYPE): Description
    """
    _fields = ["n"]

    def __init__(self, n, type=None):
        self.n = n
        self.type = type

class LitFloat(ast.AST):
    """Float
    
    Attributes:
        n (TYPE): Description
        type (TYPE): Description
    """
    _fields = ["n"]

    def __init__(self, n, type=None):
        self.n = n
        self.type = None

class LitBool(ast.AST):
    """Boolean
    
    Attributes:
        n (TYPE): Description
    """
    _fields = ["n"]

    def __init__(self, n):
        self.n = n

primops = {ast.Add: "add#", ast.Mult: "mult#"}
class Prim(ast.AST):
    """Primitive Operation
    
    Attributes:
        args (TYPE): Description
        fn (TYPE): Description
    """
    _fields = ["fn", "args"]

    def __init__(self, fn, args):
        self.fn = fn
        self.args = args

class Index(ast.AST):
    """Array indexing
    
    Attributes:
        ix (TYPE): Description
        val (TYPE): Description
    """
    _fields = ["val", "ix"]

    def __init__(self, val, ix):
        self.val = val
        self.ix = ix

class Noop(ast.AST):
    """No operation
    """
    _fields = []
