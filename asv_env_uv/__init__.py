# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="uv"`` backend via the **uv** package bindings.

Uses :func:`uv.find_uv_bin` to locate the bundled/shipped ``uv`` executable,
then drives ``uv venv`` and ``uv pip`` (not stdlib ``venv`` alone).

Core ASV does not ship in-tree ``asv.plugins.uv`` with the same ``tool_name``;
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
    find_uv_bin = None  # type: ignore[assignment]
    _HAS_UV_PKG = False

WIN = os.name == "nt"


def _resolve_uv_bin() -> str | None:
    """Return path to the uv executable via package binding, then PATH."""
    if _HAS_UV_PKG and find_uv_bin is not None:
        try:
            path = find_uv_bin()
            if path:
                return str(path)
        except Exception:
            pass
    try:
        return util.which("uv")
    except OSError:
        return None


class Uv(environment.Environment):
    """Manage an environment using the uv tool (``find_uv_bin`` / CLI)."""

    tool_name = "uv"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        self._python = python
        self._requirements = requirements
        super().__init__(conf, python, requirements, tagged_env_vars)

        self._uv_path = _resolve_uv_bin()
        if not self._uv_path:
            raise environment.EnvironmentUnavailable(
                "asv_env_uv requires the uv tool: install the 'uv' PyPI package "
                "(provides find_uv_bin) or put 'uv' on PATH"
            )

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
        return _resolve_uv_bin() is not None

    def _setup(self):
        env = dict(os.environ)
        env.update(self.build_env_vars)

        self._venv_env_vars = {"VIRTUAL_ENV": self._path}
        if "PATH" in env:
            self._venv_env_vars["PATH"] = f"{self._path}/bin:{env['PATH']}"
        else:
            self._venv_env_vars["PATH"] = f"{self._path}/bin"
        env.update(self._venv_env_vars)

        log.info(f"Creating uv venv for {self.name} via {self._uv_path}")
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
        log.info(f"Installing requirements for {self.name} with uv pip")
        self._install_requirements(env)

    def _install_requirements(self, env=None):
        if env is None:
            env = dict(os.environ)
            env.update(self.build_env_vars)

        # Prefer uv pip when available
        self._run_uv_pip(["install", "-v", "wheel", "pip>=8"], env=env)

        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                declaration = f"{key[4:]} {val}" if val else key[4:]
            else:
                declaration = f"{key} {val}" if val else key
            parsed = util.ParsedPipDeclaration(declaration)
            # construct_pip_call expects a callable like _run_pip
            util.construct_pip_call(self._run_pip, parsed)()

    def _run_uv_pip(self, args, **kwargs):
        env = kwargs.pop("env", None)
        cmd = [self._uv_path, "pip"] + list(args)
        # uv pip needs --python pointing at the env
        if "--python" not in cmd and "-p" not in cmd:
            cmd = [self._uv_path, "pip"] + list(args) + ["--python", self._path]
        return util.check_output(cmd, timeout=self._install_timeout, env=env)

    def _run_pip(self, args, **kwargs):
        # Fallback path used by construct_pip_call: python -m pip in the env
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)

    def run(self, args, **kwargs):
        joined_args = " ".join(args)
        log.debug(f"Running '{joined_args}' in {self.name}")
        return self.run_executable("python", args, **kwargs)


__all__ = ["Uv", "_resolve_uv_bin", "_HAS_UV_PKG"]
