import ast
import types
from textwrap import dedent
import inspect

from core_language import Var, Prim, Return, Fun, primops, LitBool, LitFloat, LitInt, Assign, Loop
from type_system import int32, int64

class CoreTranslator(ast.NodeVisitor):
    """
    Processes the tree of the python abstract syntax grammar,
    modifying it to convert in a new AST that can be later easly
    convert into LLVM IR( intermediate representation language )

    It recursively descends through the Python AST compressing it into our Core language. 
    We are going to support basic loops, arithmetic with addition and multiplication, 
    numeric literals, and array indexing.


    Given a function like:
    def add(a,b):
        return a + b

    Which is represent in Python's AST as:
    ('Module',
        {'body': [('FunctionDef',
                {'args': ('arguments',
                          {'args': [('Name',
                                     {'ctx': ('Param', {}), 'id': "'a'"}),
                                    ('Name',
                                     {'ctx': ('Param', {}), 'id': "'b'"})],
                           'defaults': [],
                           'kwarg': None,
                           'vararg': None}),
                 'body': [('Return',
                           {'value': ('BinOp',
                                      {'left': ('Name',
                                                {'ctx': ('Load', {}),
                                                 'id': "'a'"}),
                                       'op': ('Add', {}),
                                       'right': ('Name',
                                                 {'ctx': ('Load', {}),
                                                  'id': "'b'"})})})],
                 'decorator_list': [],
                 'name': "'add'"})]})

    To something that looks like this:
    ('Fun',
     {'args': [('Var', {'id': "'a'", 'type': None}),
               ('Var', {'id': "'b'", 'type': None})],
      'body': [('Return',
                {'val': ('Prim',
                         {'args': [('Var', {'id': "'a'", 'type': None}),
                                   ('Var', {'id': "'b'", 'type': None})],
                          'fn': "'add#'"})})],
      'fname': "'add'"})

    The type is going to be infered later on.
    """

    def __init__(self):
        pass

    def translate(self, source):
        if isinstance(source, types.ModuleType):
            source = dedent(inspect.getsource(source))
        if isinstance(source, types.FunctionType):
            source = dedent(inspect.getsource(source))
        if isinstance(source, types.LambdaType):
            source = dedent(inspect.getsource(source))
        elif isinstance(source, (str, unicode)):
            source = dedent(source)
        else:
            raise NotImplementedError

        self._source = source
        self._ast = ast.parse(source)
        return self.visit(self._ast)

    def visit_Module(self, node):
        body = map(self.visit, node.body)
        return body[0]

    def visit_Name(self, node):
        return Var(node.id)

    def visit_Num(self, node):
        if isinstance(node.n, float):
            return LitFloat(node.n)
        else:
            return LitInt(node.n)

    def visit_Bool(self, node):
        return LitBool(node.n)

    def visit_Call(self, node):
        name = self.visit(node.func)
        args = map(self.visit, node.args)
        keywords = map(self.visit, node.keywords)
        return App(name, args)

    def visit_BinOp(self, node):
        op_str = node.op.__class__
        a = self.visit(node.left)
        b = self.visit(node.right)
        opname = primops[op_str]
        return Prim(opname, [a, b])

    def visit_Assign(self, node):
        targets = node.targets

        assert len(node.targets) == 1
        var = node.targets[0].id
        val = self.visit(node.value)
        return Assign(var, val)

    def visit_FunctionDef(self, node):
        stmts = list(node.body)
        stmts = map(self.visit, stmts)
        args = map(self.visit, node.args.args)
        res = Fun(node.name, args, stmts)
        return res

    def visit_Pass(self, node):
        return Noop()

    def visit_Return(self, node):
        val = self.visit(node.value)
        return Return(val)

    def visit_Attribute(self, node):
        if node.attr == "shape":
            val = self.visit(node.value)
            return Prim("shape#", [val])
        else:
            raise NotImplementedError

    def visit_Subscript(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.slice:
                val = self.visit(node.value)
                ix = self.visit(node.slice.value)
                return Index(val, ix)
        elif isinstance(node.ctx, ast.Store):
            raise NotImplementedError

    def visit_For(self, node):
        target = self.visit(node.target)
        stmts = map(self.visit, node.body)
        if node.iter.func.id in {"xrange", "range"}:
            args = map(self.visit, node.iter.args)
        else:
            raise Exception("Loop must be over range")

        if len(args) == 1:   # xrange(n)
            return Loop(target, LitInt(0, type=int32), args[0], stmts)
        elif len(args) == 2:  # xrange(n,m)
            return Loop(target, args[0], args[1], stmts)

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Add):
            ref = node.target.id
            value = self.visit(node.value)
            return Assign(ref, Prim("add#", [Var(ref), value]))
        if isinstance(node.op, ast.Mul):
            ref = node.target.id
            value = self.visit(node.value)
            return Assign(ref, Prim("mult#", [Var(ref), value]))
        else:
            raise NotImplementedError

    def generic_visit(self, node):
        raise NotImplementedError