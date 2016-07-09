from collections import deque
from type_system import TApp, TCon, TFun, TVar, ftv

class ConstrainSolver(object):
    def empty(self):
        return {}
    def apply(self, s, t):
        if isinstance(t, TCon):
            return t
        elif isinstance(t, TApp):
            return TApp(self.apply(s, t.a), self.apply(s, t.b))
        elif isinstance(t, TFun):
            argtys = [self.apply(s, a) for a in t.argtys]
            retty = self.apply(s, t.retty)
            return TFun(argtys, retty)
        elif isinstance(t, TVar):
            return s.get(t.s, t)
    def applyList(self, s, xs):
        return [(self.apply(s, x), self.apply(s, y)) for (x, y) in xs]
    
    def unify(self, x, y):
        if isinstance(x, TApp) and isinstance(y, TApp):
            s1 = self.unify(x.a, y.a)
            s2 = self.unify(self.apply(s1, x.b), self.apply(s1, y.b))
            return self.compose(s2, s1)
        elif isinstance(x, TCon) and isinstance(y, TCon) and (x == y):
            return self.empty()
        elif isinstance(x, TFun) and isinstance(y, TFun):
            if len(x.argtys) != len(y.argtys):
                return Exception("Wrong number of arguments")
            s1 = self.solve(zip(x.argtys, y.argtys))
            s2 = self.unify(self.apply(s1, x.retty), self.apply(s1, y.retty))
            return self.compose(s2, s1)
        elif isinstance(x, TVar):
            return self.bind(x.s, y)
        elif isinstance(y, TVar):
            return self.bind(y.s, x)
        else:
            raise InferError(x, y)
    def solve(self, xs):
        mgu = self.empty()
        cs = deque(xs)
        while len(cs):
            (a, b) = cs.pop()
            s = self.unify(a, b)
            mgu = self.compose(s, mgu)
            cs = deque(self.applyList(s, cs))
        return mgu

    def bind(self, n, x):
        if x == n:
            return self.empty()
        elif self.occurs_check(n, x):
            raise InfiniteType(n, x)
        else:
            return dict([(n, x)])
    def occurs_check(self, n, x):
        return n in ftv(x)

    def union(self, s1, s2):
        nenv = s1.copy()
        nenv.update(s2)
        return nenv
    
    def compose(self, s1, s2):
        s3 = dict((t, self.apply(s1, u)) for t, u in s2.items())
        return self.union(s1, s3)