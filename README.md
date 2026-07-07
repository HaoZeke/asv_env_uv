# asv_env_uv

ASV environment backend for `environment_type = "uv"` (uv.find_uv_bin + uv venv/pip).

Core ASV (extract design) ships only **virtualenv** and **existing**.
This package is the **provider** for `uv` — there is no in-tree
`asv.plugins.uv`.

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
uv = "asv_env_uv:Uv"
```

```bash
pip install "git+https://github.com/HaoZeke/asv_env_uv.git"
```

```json
{ "environment_type": "uv" }
```

Install into the host environment that runs ASV. Conf `plugins` is optional
when entry points are registered.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
