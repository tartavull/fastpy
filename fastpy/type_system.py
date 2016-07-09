class TVar(object):
    def __init__(self, s):
        self.s = s

    def __hash__(self):
        return hash(self.s)

    def __eq__(self, other):
        if isinstance(other, TVar):
            return (self.s == other.s)
        else:
            return False

    def __str__(self):
        return self.s

class TCon(object):
    def __init__(self, s):
        self.s = s

    def __eq__(self, other):
        if isinstance(other, TCon):
            return (self.s == other.s)
        else:
            return False

    def __hash__(self):
        return hash(self.s)

    def __str__(self):
        return self.s

class TApp(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        if isinstance(other, TApp):
            return (self.a == other.a) & (self.b == other.b)
        else:
            return False

    def __hash__(self):
        return hash((self.a, self.b))

    def __str__(self):
        return str(self.a) + " " + str(self.b)

class TFun(object):
    def __init__(self, argtys, retty):
        assert isinstance(argtys, list)
        self.argtys = argtys
        self.retty = retty

    def __eq__(self, other):
        if isinstance(other, TFun):
            return (self.argtys == other.argtys) & (self.retty == other.retty)
        else:
            return False

    def __str__(self):
        return str(self.argtys) + " -> " + str(self.retty)

def ftv(x):
    """
    What was this?
    """
    if isinstance(x, TCon):
        return set()
    elif isinstance(x, TApp):
        return ftv(x.a) | ftv(x.b)
    elif isinstance(x, TFun):
        return reduce(set.union, map(ftv, x.argtys)) | ftv(x.retty)
    elif isinstance(x, TVar):
        return set([x])

def is_array(ty):
    return isinstance(ty, TApp) and ty.a == TCon("Array")

int32 = TCon("Int32")
int64 = TCon("Int64")
float32 = TCon("Float")
double64 = TCon("Double")
void = TCon("Void")
array = lambda t: TApp(TCon("Array"), t)

array_int32 = array(int32)
array_int64 = array(int64)
array_double64 = array(double64)