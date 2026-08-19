from importlib.metadata import version

import psychopy_egi_pynetstation
from psychopy_egi_pynetstation import __version__


def test_public_api_lists_wrapper_without_importing_psychopy():
    assert psychopy_egi_pynetstation.__all__ == ["EGINetStation", "__version__"]


def test_package_and_module_versions_match():
    assert version("psychopy-egi-pynetstation") == __version__
