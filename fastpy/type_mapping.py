import ctypes

import llvm.core as lc
import numpy as np

# Adapt the LLVM types to use libffi/ctypes wrapper so we can dynamically create
# the appropriate C types for our JIT'd function at runtime.
_nptypemap = {
    'i': ctypes.c_int,
    'f': ctypes.c_float,
    'd': ctypes.c_double,
}

def mangler(fname, sig):
    return fname + str(hash(tuple(sig)))

def wrap_module(sig, llfunc, engine):
    pfunc = wrap_function(llfunc, engine)
    dispatch = dispatcher(pfunc)
    return dispatch

def wrap_function(func, engine):
    args = func.type.pointee.args
    ret_type = func.type.pointee.return_type
    ret_ctype = wrap_type(ret_type)
    args_ctypes = map(wrap_type, args)

    functype = ctypes.CFUNCTYPE(ret_ctype, *args_ctypes)
    fptr = engine.get_pointer_to_function(func)

    cfunc = functype(fptr)
    cfunc.__name__ = func.name
    return cfunc

def wrap_type(llvm_type):
    kind = llvm_type.kind
    if kind == lc.TYPE_INTEGER:
        ctype = getattr(ctypes, "c_int"+str(llvm_type.width))
    elif kind == lc.TYPE_DOUBLE:
        ctype = ctypes.c_double
    elif kind == lc.TYPE_FLOAT:
        ctype = ctypes.c_float
    elif kind == lc.TYPE_VOID:
        ctype = None
    elif kind == lc.TYPE_POINTER:
        pointee = llvm_type.pointee
        p_kind = pointee.kind
        if p_kind == lc.TYPE_INTEGER:
            width = pointee.width
            if width == 8:
                ctype = ctypes.c_char_p
            else:
                ctype = ctypes.POINTER(wrap_type(pointee))
        elif p_kind == lc.TYPE_VOID:
            ctype = ctypes.c_void_p
        else:
            ctype = ctypes.POINTER(wrap_type(pointee))
    elif kind == lc.TYPE_STRUCT:
        struct_name = llvm_type.name.split('.')[-1]
        struct_name = struct_name.encode('ascii')
        struct_type = None

        if struct_type and issubclass(struct_type, ctypes.Structure):
            return struct_type

        if hasattr(struct_type, '_fields_'):
            names = struct_type._fields_
        else:
            names = ["field"+str(n) for n in range(llvm_type.element_count)]

        ctype = type(ctypes.Structure)(struct_name, (ctypes.Structure,),
                                       {'__module__': "numpile"})

        fields = [(name, wrap_type(elem))
                  for name, elem in zip(names, llvm_type.elements)]
        setattr(ctype, '_fields_', fields)
    else:
        raise Exception("Unknown LLVM type %s" % kind)
    return ctype

def wrap_ndarray(na):
    # For NumPy arrays grab the underlying data pointer. Doesn't copy.
    ctype = _nptypemap[na.dtype.char]
    _shape = list(na.shape)
    data = na.ctypes.data_as(ctypes.POINTER(ctype))
    dims = len(na.strides)
    shape = (ctypes.c_int*dims)(*_shape)
    return (data, dims, shape)

def wrap_arg(arg, val):
    if isinstance(val, np.ndarray):
        ndarray = arg._type_
        data, dims, shape = wrap_ndarray(val)
        return ndarray(data, dims, shape)
    else:
        return val

def dispatcher(fn):
    def _call_closure(*args):
        cargs = list(fn._argtypes_)
        pargs = list(args)
        rargs = map(wrap_arg, cargs, pargs)
        return fn(*rargs)
    _call_closure.__name__ = fn.__name__
    return _call_closure