Contributing and building the docs
==================================

Install the package with its documentation dependencies, then run Sphinx with
warnings treated as errors:

.. code-block:: console

   python -m pip install -e ".[docs]"
   python -m sphinx -W --keep-going -b html docs docs/_build/html

On macOS or Linux, ``make -C docs html`` is equivalent. Open
``docs/_build/html/index.html`` to inspect the result.

When a GUI option changes, update :doc:`builder-components` together with the
Component's label, hint, default, and test coverage. Verify screenshot text,
code examples, internal links, table wrapping, and mobile-width layout before
publishing.

See the repository's ``CONTRIBUTING.md`` for the development setup, pull
request checklist, hardware-validation expectations, and release process.
