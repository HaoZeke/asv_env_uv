# asv_env_uv

Drop-in ASV backend for `environment_type = "uv"`.

Creates environments with **in-process** [`uv-python`](https://crates.io/crates/uv-python)
+ [`uv-virtualenv`](https://crates.io/crates/uv-virtualenv) crate APIs via a
**maturin** wheel. Environment create does **not** shell out to a PATH `uv`
CLI binary.

## Drop-in setup

Host environment that runs ASV (design branch / release with
`asv.envmgmt.discover`):

```bash
pip install asv                    # or editable install of design branch
# build wheel on a machine with cargo + maturin (prefer a remote builder)
pip install maturin
maturin build --release
pip install target/wheels/asv_env_uv-*.whl
```

`asv.conf.json` — no `plugins` list required:

```json
{
  "version": 1,
  "project": "myproj",
  "repo": ".",
  "environment_type": "uv",
  "pythons": ["3.12"],
  "matrix": {
    "req": {
      "numpy": ["1.26"]
    }
  },
  "install_command": [
    "in-dir={env_dir} python -mpip install --no-deps {wheel_file}"
  ]
}
```

`--no-deps` keeps matrix pins meaningful when installing the project wheel
(see ASV issues #1542 / #1543 and `asv.envmgmt.matrix_layers`).

## Capabilities

| Flag | Value |
|------|-------|
| `matrix_install_mode` | `create` |
| `supports_joint_pypi_solve` | `True` |
| `supports_joint_pypi_conda_solve` | `False` |
| `project_install_prefers_no_deps` | `True` |
| `requires_host_tool` | none (in-process) |

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
uv = "asv_env_uv:Uv"
```

## Tests

```bash
pip install -e ".[test]"   # needs built extension
pytest -q
```
