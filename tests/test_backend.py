# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path

from asv_env_uv import Uv, _HAS_NATIVE


def test_tool_name():
    assert Uv.tool_name == "uv"


def test_cargo_depends_on_uv_crates():
    cargo = Path(__file__).resolve().parents[1] / "Cargo.toml"
    text = cargo.read_text()
    assert re_search_uv(text)


def re_search_uv(text: str) -> bool:
    return 'uv =' in text or 'name = "uv"' in text or "\nuv " in text or 'uv =' in text.replace(" ", "")


def test_cargo_has_uv_dep():
    text = (Path(__file__).resolve().parents[1] / "Cargo.toml").read_text()
    assert "uv =" in text or 'uv=' in text
    assert "uv-python" in text or "uv_python" in text


def test_maturin_pyproject():
    text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    assert "maturin" in text
    assert "asv_env_uv._native" in text


def test_native_or_honest_missing():
    if _HAS_NATIVE:
        from asv_env_uv import _native

        assert _native.backend_name() == "uv-crates"
        assert "uv" in _native.uv_crate_version().lower() or "asv_env_uv" in _native.uv_crate_version()
        assert callable(_native.create_venv)
    else:
        assert Uv.matches("3.12") is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "uv"}
    assert "uv" in names
