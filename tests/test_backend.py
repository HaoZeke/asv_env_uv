# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
from pathlib import Path

import asv_env_uv
from asv_env_uv import Uv, _HAS_UV_PKG, _resolve_uv_bin


def test_tool_name():
    assert Uv.tool_name == "uv"


def test_requires_uv_package_binding():
    tree = ast.parse(Path(asv_env_uv.__file__).read_text())
    imported = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "uv":
            imported.extend(a.name for a in n.names)
    assert "find_uv_bin" in imported
    src = Path(asv_env_uv.__file__).read_text()
    assert "import venv" not in src
    # no PATH-only primary fallback
    assert "util.which(\"uv\")" not in src and "util.which('uv')" not in src


def test_resolve_uv_bin_uses_binding():
    if not _HAS_UV_PKG:
        return
    path = _resolve_uv_bin()
    assert path
    assert "uv" in path.lower()


def test_matches():
    if _HAS_UV_PKG:
        assert Uv.matches("3.12") is True
    assert Uv.matches("not-a-version") is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "uv"}
    assert "uv" in names
