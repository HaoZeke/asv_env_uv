# asv_env_uv

ASV `environment_type = "uv"` as a **maturin** wheel whose Rust core depends
on the **uv** crate stack (`uv`, `uv-python`, …).

```bash
maturin build --release
pip install target/wheels/asv_env_uv-*.whl
# runtime still needs a `uv` binary co-installed (same line as the crate)
```

```json
{ "environment_type": "uv" }
```
