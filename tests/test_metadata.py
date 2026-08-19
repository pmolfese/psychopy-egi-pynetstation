from importlib.metadata import version

from psychopy_egi_pynetstation import __version__


def test_package_and_module_versions_match():
    assert version("psychopy-egi-pynetstation") == __version__

