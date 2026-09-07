"""Load custom_components/waipu/api.py and const.py directly by file path,
bypassing custom_components/waipu/__init__.py (which imports homeassistant).

Both modules are themselves free of any homeassistant import — api.py only
needs aiohttp, const.py only needs the stdlib — so their pure logic (parsing,
slot math, Program/Station selection, ...) can be unit-tested without the
full homeassistant package installed. Anything that actually touches HA
(config_flow, coordinator, entity platforms) is out of scope for this
loader; those need the real package/pytest-homeassistant-custom-component
and are not covered by this test tier.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

_WAIPU_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "waipu"


def _load(name: str) -> types.ModuleType:
    module_name = f"waipu_{name}"
    spec = importlib.util.spec_from_file_location(module_name, _WAIPU_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Must be registered before exec — dataclasses' KW_ONLY detection (and
    # anything else doing sys.modules[cls.__module__] lookups) needs to
    # find the module by name while it's executing, not just afterward.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


api = _load("api")
const = _load("const")
