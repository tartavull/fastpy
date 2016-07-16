#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_fastpy
----------------------------------

Tests for `fastpy` module.
"""

import pytest


from fastpy.fastpy import fast


class TestFastpy(object):

    @classmethod
    def setup_class(cls):
        pass

    def test_simple_return(self):

        @fast
        def a():
            return 1
        assert a() == 1


        @fast
        def b():
            return 1.0
        assert a() == 1.0

    def test_add(self):
        
        @fast
        def add(x,y):
          return x + y

        assert add(2,3) == 5
        assert add(2.0, 3.0) == 5.0

    @classmethod
    def teardown_class(cls):
        pass

