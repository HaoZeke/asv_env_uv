# asv_env_uv

ASV `environment_type = "uv"` using the official **uv** package (maturin/Rust
wheel from Astral) and `uv.find_uv_bin()` — not stdlib `venv`, not a PATH-only
guess without the package.

```bash
pip install "git+https://github.com/HaoZeke/asv_env_uv.git"
# pulls dependency: uv (Rust binary + Python binding)
```

```json
{ "environment_type": "uv" }
```
