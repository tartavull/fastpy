===============================
fastpy
===============================


.. image:: https://img.shields.io/pypi/v/fastpy.svg
        :target: https://pypi.python.org/pypi/fastpy

.. image:: https://img.shields.io/travis/tartavull/fastpy.svg
        :target: https://travis-ci.org/tartavull/fastpy

.. image:: https://readthedocs.org/projects/fastpy/badge/?version=latest
        :target: https://fastpy.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/tartavull/fastpy/shield.svg
     :target: https://pyup.io/repos/github/tartavull/fastpy/
     :alt: Updates

Python made fast.
Decorate your functions with @fast, we will infered the types
you used, compile to machine code, and execute.


* Free software: MIT license
* Documentation: https://fastpy.readthedocs.io.


Biased test showing how fast fastpy is:
---------------------------------------

Initial code:

.. code-block:: python

    def long_loop(a):
      for i in range(100000):
        for j in range(10000):
          a += 1
    return a
    print long_loop(0)



.. code-block:: bash

    $ time python loop.py 
    1000000000
    python test.py  39.24s user 0.01s system 99% cpu 39.420 total



.. code-block:: bash

    $ time pypy loop.py   
    1000000000
    pypy test.py  0.92s user 0.01s system 99% cpu 0.937 total

Now we modify the code to use fastpy

.. code-block:: python

    from fastpy import fast

    @fast
    def long_loop(a):
      for i in range(100000):
        for j in range(10000):
          a += 1
      return a
    print long_loop(0)


.. code-block:: bash

    $  time python loop.py 
    1000000000
    python test.py  0.11s user 0.00s system 99% cpu 0.117 total


Credits
---------
Based on this tutorial http://dev.stephendiehl.com/numpile/
