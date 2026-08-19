"""Sphinx configuration for PsychoPy EGI NetStation."""

from pathlib import Path
import sys
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from psychopy_egi_pynetstation import __version__  # noqa: E402


# Documentation builders should not need PsychoPy's full GUI dependency stack.
# A normal Sphinx mock cannot model BaseDevice's class keyword (``aliases``),
# so provide the small import surface used by the hardware wrapper when
# PsychoPy is unavailable.
try:  # pragma: no cover - depends on the documentation build environment
    import psychopy  # noqa: F401
except ImportError:  # pragma: no cover
    psychopy = ModuleType("psychopy")
    psychopy_hardware = ModuleType("psychopy.hardware")
    psychopy_hardware_base = ModuleType("psychopy.hardware.base")
    psychopy_logging = ModuleType("psychopy.logging")

    class BaseDevice:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()

    psychopy_hardware_base.BaseDevice = BaseDevice
    psychopy_hardware.base = psychopy_hardware_base
    psychopy.logging = psychopy_logging
    for level in ("info", "warning", "error"):
        setattr(psychopy_logging, level, lambda *args, **kwargs: None)

    sys.modules["psychopy"] = psychopy
    sys.modules["psychopy.hardware"] = psychopy_hardware
    sys.modules["psychopy.hardware.base"] = psychopy_hardware_base
    sys.modules["psychopy.logging"] = psychopy_logging


project = "PsychoPy EGI NetStation"
author = "Peter J. Molfese, NIH CMN"
copyright = "2026, Peter J. Molfese, NIH CMN"
version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = ".rst"
root_doc = "index"

html_theme = "alabaster"
html_static_path = ["_static"]
html_title = f"{project} {release}"
html_theme_options = {
    "description": "PsychoPy Builder and Python support for EGI/Magstim NetStation",
    "fixed_sidebar": True,
    "github_button": True,
    "github_user": "pmolfese",
    "github_repo": "psychopy-egi-pynetstation",
}

autodoc_member_order = "bysource"
napoleon_numpy_docstring = True
napoleon_google_docstring = False
