# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="uv"`` — maturin wheel over **uv-python** / **uv-virtualenv**.

Create path calls ``asv_env_uv._native.create_venv_inprocess``, which uses
``PythonInstallation::find_existing`` + ``uv_virtualenv::create_venv`` in-process.
It does **not** shell out to a PATH ``uv`` binary for environment creation.
"""

from __future__ import annotations

import re
from pathlib import Path

from asv import environment, util
from asv.console import log

try:
    from asv_env_uv import _native as _native

    _HAS_NATIVE = True
except ImportError:  # pragma: no cover
    _native = None
    _HAS_NATIVE = False


class Uv(environment.Environment):
    """Manage an environment via in-process uv-virtualenv (maturin extension)."""

    tool_name = "uv"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        if not _HAS_NATIVE:
            raise environment.EnvironmentUnavailable(
                "asv_env_uv requires the maturin-built extension linking "
                "uv-python + uv-virtualenv (maturin build --release on a builder)"
            )
        if not _native.uses_inprocess_uv_virtualenv():
            raise environment.EnvironmentUnavailable(
                "asv_env_uv extension is not the in-process uv-virtualenv build"
            )
        self._python = python
        self._requirements = requirements
        super().__init__(conf, python, requirements, tagged_env_vars)

    @property
    def name(self):
        python = self._python
        if self._python.startswith("pypy"):
            python = python[2:]
        return environment.get_env_name(
            self.tool_name, python, self._requirements, self._tagged_env_vars
        )

    @classmethod
    def matches(cls, python):
        if not _HAS_NATIVE:
            return False
        return bool(re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python))

    def _setup(self):
        log.info(
            f"Creating uv env for {self.name} via in-process uv-virtualenv "
            f"({_native.backend_name()}, {_native.uv_crate_version()})"
        )
        Path(self._path).mkdir(parents=True, exist_ok=True)
        _native.create_venv_inprocess(self._path, self._python)
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                req = f"{key[4:]}{('==' + val) if val else ''}"
            else:
                req = f"{key}{('==' + val) if val else ''}"
            try:
                _native.pip_install_in_prefix(
                    self._path, req if (val or key.startswith("pip+")) else key
                )
            except Exception:
                declaration = f"{key[4:] if key.startswith('pip+') else key} {val}".strip()
                parsed = util.ParsedPipDeclaration(declaration)
                util.construct_pip_call(self._run_pip, parsed)()

    def run(self, args, **kwargs):
        log.debug(f"Running '{' '.join(args)}' in {self.name}")
        return self.run_executable("python", args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Uv", "_HAS_NATIVE"]
