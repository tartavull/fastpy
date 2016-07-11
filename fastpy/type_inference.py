import string

from type_system import TVar, TFun, int32, int64

class TypeInfer(object):
    """
    For type inference we wish to take our untyped core AST and overlay types 
    deduced from two sources:
      * Types intrinsic to the operations in use
      * User input types

    We will walk our AST generating a constraint set of equality relations
    between types, which will give rise to a large constraint problem
    we will solve when given a set of input types for arguments.

    There are four possible outcomes:
      * The types are correctly determined.
      * The types are underdetermined.
      * The types is polymorphic.
      * The types are inconsistent.


    Converts the example from core translator into, which in this case is polymorphic,
    This is good for code reuse and implies we get a whole family of functions.

    ('Fun',
     {'args': [('Var',
                {'id': "'a'",
                 'type': TVar("$a")}),
               ('Var',
                {'id': "'b'",
                 'type': TVar("$b")})],
      'body': [('Return',
                {'val': ('Prim',
                         {'args': [('Var',
                                    {'id': "'a'",
                                     'type': TVar("$a")}),
                                   ('Var',
                                    {'id': "'b'",
                                     'type':TVar("$b")})],
                          'fn': "'add#'"})})],
      'fname': "'add'"})


        Another example:
        def addup(n):
            x = 1
            for i in range(n):
                n += 1 + x
            return n

        Represented as core AST:
        ('Fun',
         {'args': [('Var', {'id': "'n'", 'type': $a})],
          'body': [('Assign',
                    {'ref': "'x'", 'type': $b, 'val': ('LitInt', {'n': 1})}),
                   ('Loop',
                    {'begin': ('LitInt', {'n': 0}),
                     'body': [('Assign',
                               {'ref': "'n'",
                                'type': $b,
                                'val': ('Prim',
                                        {'args': [('Var',
                                                   {'id': "'n'",
                                                    'type': $a}),
                                                  ('Prim',
                                                   {'args': [('LitInt',
                                                              {'n': 1}),
                                                             ('Var',
                                                              {'id': "'x'",
                                                               'type': $b})],
                                                    'fn': "'add#'"})],
                                         'fn': "'add#'"})})],
                     'end': ('Var', {'id': "'n'", 'type': $a}),
                     'var': ('Var', {'id': "'i'", 'type': Int32})}),
                   ('Return', {'val': ('Var', {'id': "'n'", 'type': $b})})],
          'fname': "'addup'"})
    
        Produces this constraints:
        Int32 ~ Int32
        $c ~ Int64
        $a ~ Int32
        $d ~ $b
        $a ~ $b
        $b ~ $a
        $b ~ $retty



    """

    def __init__(self):
        self.constraints = []
        self.env = {}
        self.names = self.naming()

    def naming(self):
        """Generate names for variables
        
        Returns:
            TYPE: Description
        """
        k = 0
        while True:
            for a in string.ascii_lowercase:
                yield ("'"+a+str(k)) if (k > 0) else (a)
            k = k+1

    def fresh(self):
        return TVar('$' + next(self.names))  # New meta type variable.

    def visit(self, node):
        name = "visit_%s" % type(node).__name__
        if hasattr(self, name):
            return getattr(self, name)(node)
        else:
            return self.generic_visit(node)

    def visit_Fun(self, node):
        arity = len(node.args)
        self.argtys = [self.fresh() for v in node.args]
        self.retty = TVar("$retty")
        for (arg, ty) in zip(node.args, self.argtys):
            arg.type = ty
            self.env[arg.id] = ty
        map(self.visit, node.body)
        return TFun(self.argtys, self.retty)

    def visit_Noop(self, node):
        return None

    def visit_LitInt(self, node):
        tv = self.fresh()
        node.type = tv
        return tv

    def visit_LitFloat(self, node):
        tv = self.fresh()
        node.type = tv
        return tv

    def visit_Assign(self, node):
        ty = self.visit(node.val)
        if node.ref in self.env:
            # Subsequent uses of a variable must have the same type.
            self.constraints += [(ty, self.env[node.ref])]
        self.env[node.ref] = ty
        node.type = ty
        return None

    def visit_Index(self, node):
        tv = self.fresh()
        ty = self.visit(node.val)
        ixty = self.visit(node.ix)
        self.constraints += [(ty, array(tv)), (ixty, int32)]
        return tv

    def visit_Prim(self, node):
        if node.fn == "shape#":
            return array(int32)
        elif node.fn == "mult#":
            tya = self.visit(node.args[0])
            tyb = self.visit(node.args[1])
            self.constraints += [(tya, tyb)]
            return tyb
        elif node.fn == "add#":
            tya = self.visit(node.args[0])
            tyb = self.visit(node.args[1])
            self.constraints += [(tya, tyb)]
            return tyb
        else:
            raise NotImplementedError

    def visit_Var(self, node):
        ty = self.env[node.id]
        node.type = ty
        return ty

    def visit_Return(self, node):
        ty = self.visit(node.val)
        self.constraints += [(ty, self.retty)]

    def visit_Loop(self, node):
        self.env[node.var.id] = int32
        varty = self.visit(node.var)
        begin = self.visit(node.begin)
        end = self.visit(node.end)
        self.constraints += [(varty, int32), (
            begin, int64), (end, int32)]
        map(self.visit, node.body)

    def generic_visit(self, node):
        raise NotImplementedError

class UnderDeteremined(Exception):
    def __str__(self):
        return "The types in the function are not fully determined by the input types. Add annotations."

class InferError(Exception):
    def __init__(self, ty1, ty2):
        self.ty1 = ty1
        self.ty2 = ty2

    def __str__(self):
        return '\n'.join([
            "Type mismatch: ",
            "Given: ", "\t" + str(self.ty1),
            "Expected: ", "\t" + str(self.ty2)
        ])