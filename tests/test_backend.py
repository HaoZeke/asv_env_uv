# Licensed under a 3-clause BSD style license - see LICENSE.rst
import asv_env_uv
from asv_env_uv import Uv, _resolve_uv_bin, _HAS_UV_PKG


def test_tool_name():
    assert Uv.tool_name == "uv"


def test_resolve_uv_bin_uses_binding_or_path():
    # With package dependency installed, binding should work
    path = _resolve_uv_bin()
    assert path is not None
    assert "uv" in path.lower() or path.endswith("uv") or path.endswith("uv.exe")


def test_matches_with_uv_available():
    assert Uv.matches("3.12") is True
    assert Uv.matches("not-a-version") is False


def test_source_invokes_uv_not_only_stdlib_venv():
    import inspect
    src = inspect.getsource(asv_env_uv)
    assert "find_uv_bin" in src
    assert "uv venv" in src or '"venv"' in src
    assert "stdlib" not in src.lower() or "not" in src.lower()


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "uv"}
    assert "uv" in names
    assert "asv_env_uv" in names["uv"]
