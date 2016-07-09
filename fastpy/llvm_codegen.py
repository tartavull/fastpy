from collections import defaultdict

import llvm.core as lc
from llvm.core import Module, Builder, Function, Type, Constant

from type_system import int32, int64, double64, float32, array_int32, array_int64, array_double64, ftv, is_array , TVar
from type_mapping import mangler

pointer     = Type.pointer
int_type    = Type.int()
float_type  = Type.float()
double_type = Type.double()
bool_type   = Type.int(1)
void_type   = Type.void()
void_ptr    = pointer(Type.int(8))

def array_type(elt_type):
    return Type.struct([
        pointer(elt_type),  # data
        int_type,           # dimensions
        pointer(int_type),  # shape
    ], name='ndarray_' + str(elt_type))

int32_array = pointer(array_type(int_type))
int64_array = pointer(array_type(Type.int(64)))
double_array = pointer(array_type(double_type))

lltypes_map = {
    int32          : int_type,
    int64          : int_type,
    float32        : float_type,
    double64       : double_type,
    array_int32    : int32_array,
    array_int64    : int64_array,
    array_double64 : double_array
}

def to_lltype(ptype):
    return lltypes_map[ptype]

def determined(ty):
    return len(ftv(ty)) == 0

class LLVMEmitter(object):
    def __init__(self, module, spec_types, retty, argtys):
        self.module = module
        self.function = None             # LLVM Function
        self.builder = None              # LLVM Builder
        self.locals = {}                 # Local variables
        self.arrays = defaultdict(dict)  # Array metadata
        self.exit_block = None           # Exit block
        self.spec_types = spec_types     # Type specialization
        self.retty = retty               # Return type
        self.argtys = argtys             # Argument types

    def start_function(self, name, rettype, argtypes):
        func_type = lc.Type.function(rettype, argtypes, False)
        function = lc.Function.new(self.module, func_type, name)
        entry_block = function.append_basic_block("entry")
        builder = lc.Builder.new(entry_block)
        self.exit_block = function.append_basic_block("exit")
        self.function = function
        self.builder = builder

    def end_function(self):
        self.builder.position_at_end(self.exit_block)

        if 'retval' in self.locals:
            retval = self.builder.load(self.locals['retval'])
            self.builder.ret(retval)
        else:
            self.builder.ret_void()

    def add_block(self, name):
        return self.function.append_basic_block(name)

    def set_block(self, block):
        self.block = block
        self.builder.position_at_end(block)

    def cbranch(self, cond, true_block, false_block):
        self.builder.cbranch(cond, true_block, false_block)

    def branch(self, next_block):
        self.builder.branch(next_block)

    def specialize(self, val):
        if isinstance(val.type, TVar):
            return to_lltype(self.spec_types[val.type.s])
        else:
            return val.type

    def const(self, val):
        if isinstance(val, (int, long)):
            return Constant.int(int_type, val)
        elif isinstance(val, float):
            return Constant.real(double_type, val)
        elif isinstance(val, bool):
            return Constant.int(bool_type, int(val))
        elif isinstance(val, str):
            return Constant.stringz(val)
        else:
            raise NotImplementedError

    def visit_LitInt(self, node):
        ty = self.specialize(node)
        if ty is double_type:
            return Constant.real(double_type, node.n)
        elif ty == int_type:
            return Constant.int(int_type, node.n)

    def visit_LitFloat(self, node):
        ty = self.specialize(node)
        if ty is double_type:
            return Constant.real(double_type, node.n)
        elif ty == int_type:
            return Constant.int(int_type, node.n)

    def visit_Noop(self, node):
        pass

    def visit_Fun(self, node):
        rettype = to_lltype(self.retty)
        argtypes = map(to_lltype, self.argtys)
        # Create a unique specialized name
        func_name = mangler(node.fname, self.argtys)
        self.start_function(func_name, rettype, argtypes)

        for (ar, llarg, argty) in zip(node.args, self.function.args, self.argtys):
            name = ar.id
            llarg.name = name

            if is_array(argty):
                zero = self.const(0)
                one = self.const(1)
                two = self.const(2)

                data = self.builder.gep(llarg, [
                                        zero, zero], name=(name + '_data'))
                dims = self.builder.gep(llarg, [
                                        zero, one], name=(name + '_dims'))
                shape = self.builder.gep(llarg, [
                                         zero, two], name=(name + '_strides'))

                self.arrays[name]['data'] = self.builder.load(data)
                self.arrays[name]['dims'] = self.builder.load(dims)
                self.arrays[name]['shape'] = self.builder.load(shape)
                self.locals[name] = llarg
            else:
                argref = self.builder.alloca(to_lltype(argty))
                self.builder.store(llarg, argref)
                self.locals[name] = argref

        # Setup the register for return type.
        if rettype is not void_type:
            self.locals['retval'] = self.builder.alloca(rettype, name="retval")

        map(self.visit, node.body)
        self.end_function()

    def visit_Index(self, node):
        if isinstance(node.val, Var) and node.val.id in self.arrays:
            val = self.visit(node.val)
            ix = self.visit(node.ix)
            dataptr = self.arrays[node.val.id]['data']
            ret = self.builder.gep(dataptr, [ix])
            return self.builder.load(ret)
        else:
            val = self.visit(node.val)
            ix = self.visit(node.ix)
            ret = self.builder.gep(val, [ix])
            return self.builder.load(ret)

    def visit_Var(self, node):
        return self.builder.load(self.locals[node.id])

    def visit_Return(self, node):
        val = self.visit(node.val)
        if val.type != void_type:
            self.builder.store(val, self.locals['retval'])
        self.builder.branch(self.exit_block)

    def visit_Loop(self, node):
        init_block = self.function.append_basic_block('for.init')
        test_block = self.function.append_basic_block('for.cond')
        body_block = self.function.append_basic_block('for.body')
        end_block = self.function.append_basic_block("for.end")

        self.branch(init_block)
        self.set_block(init_block)

        start = self.visit(node.begin)
        stop = self.visit(node.end)
        step = 1

        # Setup the increment variable
        varname = node.var.id
        inc = self.builder.alloca(int_type, name=varname)
        self.builder.store(start, inc)
        self.locals[varname] = inc

        # Setup the loop condition
        self.branch(test_block)
        self.set_block(test_block)
        cond = self.builder.icmp(lc.ICMP_SLT, self.builder.load(inc), stop)
        self.builder.cbranch(cond, body_block, end_block)

        # Generate the loop body
        self.set_block(body_block)
        map(self.visit, node.body)

        # Increment the counter
        succ = self.builder.add(self.const(step), self.builder.load(inc))
        self.builder.store(succ, inc)

        # Exit the loop
        self.builder.branch(test_block)
        self.set_block(end_block)

    def visit_Prim(self, node):
        if node.fn == "shape#":
            ref = node.args[0]
            shape = self.arrays[ref.id]['shape']
            return shape
        elif node.fn == "mult#":
            a = self.visit(node.args[0])
            b = self.visit(node.args[1])
            if a.type == double_type:
                return self.builder.fmul(a, b)
            else:
                return self.builder.mul(a, b)
        elif node.fn == "add#":
            a = self.visit(node.args[0])
            b = self.visit(node.args[1])
            if a.type == double_type:
                return self.builder.fadd(a, b)
            else:
                return self.builder.add(a, b)
        else:
            raise NotImplementedError

    def visit_Assign(self, node):
        # Subsequent assignment
        if node.ref in self.locals:
            name = node.ref
            var = self.locals[name]
            val = self.visit(node.val)
            self.builder.store(val, var)
            self.locals[name] = var
            return var

        # First assignment
        else:
            name = node.ref
            val = self.visit(node.val)
            ty = self.specialize(node)
            var = self.builder.alloca(ty, name=name)
            self.builder.store(val, var)
            self.locals[name] = var
            return var

    def visit(self, node):
        name = "visit_%s" % type(node).__name__
        if hasattr(self, name):
            return getattr(self, name)(node)
        else:
            return self.generic_visit(node)