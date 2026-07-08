# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="uv"`` via the official **uv** maturin/Rust package.

Requires the PyPI ``uv`` distribution (ships the Rust binary +
:func:`uv.find_uv_bin`). Create/install call that binary only — never stdlib
``venv`` and never an unvalidated PATH ``uv`` without the package binding.

Core ASV does not ship this backend in-tree; this package is the provider.
"""

from __future__ import annotations

import os
import re

from asv import environment, util
from asv.console import log

try:
    from uv import find_uv_bin

    _HAS_UV_PKG = True
except ImportError:  # pragma: no cover
    find_uv_bin = None  # type: ignore[misc, assignment]
    _HAS_UV_PKG = False

WIN = os.name == "nt"


def _resolve_uv_bin() -> str:
    """Return path to the **package-shipped** Rust uv binary. Fail closed."""
    if not _HAS_UV_PKG or find_uv_bin is None:
        raise environment.EnvironmentUnavailable(
            "asv_env_uv requires the official 'uv' PyPI package (maturin/Rust "
            "wheel providing find_uv_bin). Install: pip install 'uv>=0.4'"
        )
    try:
        path = find_uv_bin()
    except Exception as err:  # pragma: no cover
        raise environment.EnvironmentUnavailable(
            f"uv.find_uv_bin() failed: {err}"
        ) from err
    if not path:
        raise environment.EnvironmentUnavailable("uv.find_uv_bin() returned empty path")
    return str(path)


class Uv(environment.Environment):
    """Manage an environment using the Rust uv tool via the official package binding."""

    tool_name = "uv"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        self._python = python
        self._requirements = requirements
        # Resolve binding before super so failure is EnvironmentUnavailable
        self._uv_path = _resolve_uv_bin()
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
        if not (re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python)):
            return False
        try:
            _resolve_uv_bin()
            return True
        except environment.EnvironmentUnavailable:
            return False

    def _setup(self):
        # Always re-resolve through the package binding (no PATH-only shortcut)
        self._uv_path = _resolve_uv_bin()
        env = dict(os.environ)
        env.update(self.build_env_vars)
        self._venv_env_vars = {"VIRTUAL_ENV": self._path}
        if "PATH" in env:
            self._venv_env_vars["PATH"] = f"{self._path}/bin:{env['PATH']}"
        else:
            self._venv_env_vars["PATH"] = f"{self._path}/bin"
        env.update(self._venv_env_vars)

        log.info(f"Creating uv venv for {self.name} via find_uv_bin -> {self._uv_path}")
        util.check_call(
            [
                self._uv_path,
                "venv",
                f"--python={self._python}",
                "--no-project",
                "--seed",
                self._path,
            ],
            env=env,
        )
        log.info(f"Installing requirements for {self.name} with uv pip (Rust uv)")
        self._install_requirements(env)

    def _install_requirements(self, env=None):
        if env is None:
            env = dict(os.environ)
            env.update(self.build_env_vars)
        # Prefer uv pip (same Rust binary) for bootstrapping tools in the env
        self._run_uv_pip(["install", "-v", "wheel", "pip>=8"], env=env)
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                declaration = f"{key[4:]} {val}" if val else key[4:]
            else:
                declaration = f"{key} {val}" if val else key
            parsed = util.ParsedPipDeclaration(declaration)
            # Use uv pip for matrix installs when possible
            self._uv_pip_declaration(parsed, env=env)

    def _uv_pip_declaration(self, parsed, env=None):
        """Install one ParsedPipDeclaration via the Rust uv binary."""
        # Fall back to construct_pip_call -> python -m pip only for complex forms
        # that uv pip may not mirror; simple name/version go through uv pip.
        try:
            # util.construct_pip_call builds a closure; prefer direct uv when simple
            util.construct_pip_call(
                lambda args, **kw: self._run_uv_pip(list(args), env=env),
                parsed,
            )()
        except Exception:
            util.construct_pip_call(self._run_pip, parsed)()

    def _run_uv_pip(self, args, **kwargs):
        env = kwargs.pop("env", None)
        cmd = [self._uv_path, "pip", *list(args), "--python", self._path]
        return util.check_output(cmd, timeout=self._install_timeout, env=env)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)

    def run(self, args, **kwargs):
        joined_args = " ".join(args)
        log.debug(f"Running '{joined_args}' in {self.name}")
        return self.run_executable("python", args, **kwargs)


__all__ = ["Uv", "_resolve_uv_bin", "_HAS_UV_PKG"]
