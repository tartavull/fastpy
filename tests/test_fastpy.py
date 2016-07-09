#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_fastpy
----------------------------------

Tests for `fastpy` module.
"""

import pytest


from fastpy import fastpy


class TestFastpy(object):

    @classmethod
    def setup_class(cls):
        pass

    def test_add(self):
        
        @fastpy.fast
        def add(x,y):
          return x + y

        assert add(2,3) == 5
        assert add(2.0, 3.0) == 5.0

    @classmethod
    def teardown_class(cls):
        pass

