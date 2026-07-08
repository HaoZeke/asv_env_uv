# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path

from asv_env_uv import Uv, _HAS_NATIVE


def test_tool_name():
    assert Uv.tool_name == "uv"


def test_cargo_depends_on_uv_library_crates():
    text = (Path(__file__).resolve().parents[1] / "Cargo.toml").read_text()
    assert "uv-python" in text or "uv_python" in text
    assert "uv-virtualenv" in text or "uv_virtualenv" in text
    assert "crate-type" in text and "cdylib" in text


def test_rust_source_is_inprocess_not_path_cli():
    """Fail if create is still Command-to-PATH-uv theater."""
    src = (Path(__file__).resolve().parents[1] / "src" / "lib.rs").read_text()
    assert "uv_virtualenv::create_venv" in src or "create_venv(" in src
    assert "PythonInstallation::find" in src or "find_existing" in src
    # ban PATH-uv CLI driver for create
    assert "find_uv_executable" not in src
    assert "ASV_UV_BIN" not in src
    assert 'Command::new(&uv_bin)' not in src
    assert 'args(["venv"' not in src and 'args([\n            "venv"' not in src


def test_maturin_pyproject():
    text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    assert "maturin" in text
    assert "asv_env_uv._native" in text


def test_native_inprocess_api():
    if not _HAS_NATIVE:
        assert Uv.matches("3.12") is False
        return
    from asv_env_uv import _native

    assert _native.backend_name() == "uv-virtualenv-crates"
    assert _native.uses_inprocess_uv_virtualenv() is True
    assert "in-process" in _native.uv_crate_version().lower() or "virtualenv" in _native.uv_crate_version().lower()
    assert callable(_native.create_venv_inprocess)
    assert not hasattr(_native, "create_venv") or not callable(
        getattr(_native, "find_uv_executable", None)
    )


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    assert any(ep.name == "uv" for ep in group)
