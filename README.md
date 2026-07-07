# asv_env_uv

ASV environment backend for `environment_type = "uv"`.

Uses the **`uv` Python package** binding [`find_uv_bin()`](https://pypi.org/project/uv/)
to locate the shipped `uv` binary, then runs **`uv venv`** / **`uv pip`**.
This is **not** a stdlib-`venv` alias.

## Stage-1 discovery

```toml
[project.entry-points."asv.environment_backends"]
uv = "asv_env_uv:Uv"
```

```bash
pip install "git+https://github.com/HaoZeke/asv_env_uv.git"
# pulls the `uv` dependency which provides find_uv_bin
```

```json
{ "environment_type": "uv" }
```

## Conflict with in-tree ASV

Stage-1 ASV may also ship `asv.plugins.uv` with `tool_name = "uv"`.
**In-tree registration wins** when both are present. This package is the
extract / fallback when optional in-tree backends are omitted, and demonstrates
using the official `uv` package binding rather than relying only on `PATH`.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
