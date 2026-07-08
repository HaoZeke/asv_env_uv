# asv_env_uv

ASV `environment_type = "uv"` as a **maturin** wheel whose Rust core calls
**in-process** `uv-python` + `uv-virtualenv` crate APIs
(`PythonInstallation::find_existing` + `uv_virtualenv::create_venv`).

Environment create does **not** shell out to a PATH `uv` CLI binary.

```bash
# build on a machine with cargo+maturin (e.g. remote builder)
maturin build --release
pip install target/wheels/asv_env_uv-*.whl
```

```json
{ "environment_type": "uv" }
```
