# -*- coding: utf-8 -*-
import logging 
import sys
import numpy as np
from itertools import tee, izip

import llvm.core as lc
import llvm.passes as lp
import llvm.ee as le

from core_translator import CoreTranslator
from type_inference import TypeInfer, UnderDeteremined
from type_system import TVar, TFun, int32, int64, double64, float32
from pretty_printer import dump
from constrain_solver import ConstrainSolver 
from llvm_codegen import determined, LLVMEmitter
from type_mapping import mangler, wrap_module

logging.basicConfig(level=logging.WARN)
import ast
import inspect

module = lc.Module.new('fastpy.module')
engine = None
function_cache = {}

tm = le.TargetMachine.new(features='', cm=le.CM_JITDEFAULT)
eb = le.EngineBuilder.new(module)
engine = eb.create(tm)

def fast(fn):
    """
    Decorator which maps the function through translator, does type inference,
    and the creates a closure which when called will automatically specialize
    the function to the given argument types and compile a new version if needed.

    We will cache based on the arguments ( which entirely define the function )
    and whenever a similar typed argument set is passed we just lookup 
    the preJIT'd function and invoke it without recompiling.

    Args:
        fn (function): Function which we want to decorate
    """
    # debug(dump(ast.parse(inspect.getsource(fn))))
    core_ast = CoreTranslator().translate(fn)
    debug(dump(core_ast))
    ty, mgu = typeinfer(core_ast)
    debug(dump(core_ast))
    return specialize(core_ast, ty, mgu)

def typeinfer(core_ast):
    """Infer types
    
    Args:
        core_ast (ast): Untyped abstract syntax tree transfromed by the core translator
    
    Returns:
        TYPE: Description
    """
    infer = TypeInfer()
    ty = infer.visit(core_ast)
    mgu = ConstrainSolver().solve(infer.constraints)
    infer_ty = ConstrainSolver().apply(mgu, ty)
    debug('infered types:'+ str(infer_ty))
    debug(mgu)
    debug(infer.constraints)
    return (infer_ty, mgu)


def arg_pytype(arg):
    if isinstance(arg, np.ndarray):
        if arg.dtype == np.dtype('int32'):
            return array(int32)
        elif arg.dtype == np.dtype('int64'):
            return array(int64)
        elif arg.dtype == np.dtype('double'):
            return array(double64)
        elif arg.dtype == np.dtype('float'):
            return array(float32)
    elif isinstance(arg, int) & (arg < sys.maxint):
        return int64
    elif isinstance(arg, float):
        return double64
    else:
        raise Exception("Type not supported: %s" % type(arg))

def specialize(ast, infer_ty, mgu):
    def _wrapper(*args):
        types = map(arg_pytype, list(args))
        spec_ty = TFun(argtys=types, retty=TVar("$retty"))
        unifier = ConstrainSolver().unify(infer_ty, spec_ty)
        specializer = ConstrainSolver().compose(unifier, mgu)

        retty = ConstrainSolver().apply(specializer, TVar("$retty"))
        argtys = [ConstrainSolver().apply(specializer, ty) for ty in types]
        debug('Specialized Function:' + str(TFun(argtys, retty)))

        if determined(retty) and all(map(determined, argtys)):
            key = mangler(ast.fname, argtys)
            # Don't recompile after we've specialized.
            if key in function_cache:
                return function_cache[key](*args)
            else:
                llfunc = codegen(ast, specializer, retty, argtys)
                pyfunc = wrap_module(argtys, llfunc, engine)
                function_cache[key] = pyfunc
                return pyfunc(*args)
        else:
            raise UnderDeteremined()
    return _wrapper



def codegen(ast, specializer, retty, argtys):
    cgen = LLVMEmitter(module, specializer, retty, argtys)
    mod = cgen.visit(ast)
    cgen.function.verify()

    tm = le.TargetMachine.new(opt=3, cm=le.CM_JITDEFAULT, features='')
    pms = lp.build_pass_managers(tm=tm,
                                 fpm=False,
                                 mod=module,
                                 opt=3,
                                 vectorize=False,
                                 loop_vectorize=True)
    pms.pm.run(module)

    debug(cgen.function)
    debug(module.to_native_assembly())
    return cgen.function

def debug(fmt, *args):
    logging.debug('=' * 80)
    logging.debug(fmt, *args)