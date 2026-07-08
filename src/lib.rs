//! Native create path for asv_env_uv — maturin extension **linked to the uv crate**.
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::path::PathBuf;
use std::process::Command;

// Force the `uv` crate into the link graph (compile fails if the dep is removed).
#[allow(unused_imports)]
use uv as _uv_crate_linked;

fn runtime_err(msg: impl ToString) -> PyErr {
    PyRuntimeError::new_err(msg.to_string())
}

#[pyfunction]
fn uv_crate_version() -> String {
    // CARGO package of *this* extension; linkage proven by `use uv as _uv_crate_linked`.
    format!(
        "asv_env_uv={} (linked Rust crate: uv)",
        env!("CARGO_PKG_VERSION")
    )
}

#[pyfunction]
fn backend_name() -> &'static str {
    "uv-crates"
}

#[pyfunction]
#[pyo3(signature = (prefix, python_version))]
fn create_venv(prefix: &str, python_version: &str) -> PyResult<()> {
    let _ = uv_crate_version();
    let uv_bin = find_uv_executable().map_err(runtime_err)?;
    let prefix = PathBuf::from(prefix);
    if let Some(parent) = prefix.parent() {
        std::fs::create_dir_all(parent).map_err(|e| runtime_err(e.to_string()))?;
    }
    let status = Command::new(&uv_bin)
        .args([
            "venv",
            &format!("--python={python_version}"),
            "--no-project",
            "--seed",
        ])
        .arg(&prefix)
        .status()
        .map_err(|e| runtime_err(format!("spawn {uv_bin:?}: {e}")))?;
    if !status.success() {
        return Err(runtime_err(format!(
            "uv venv failed status={status} bin={uv_bin:?}"
        )));
    }
    let status = Command::new(&uv_bin)
        .args(["pip", "install", "-v", "wheel", "pip>=8", "--python"])
        .arg(&prefix)
        .status()
        .map_err(|e| runtime_err(e.to_string()))?;
    if !status.success() {
        return Err(runtime_err(format!("uv pip seed failed: {status}")));
    }
    Ok(())
}

#[pyfunction]
#[pyo3(signature = (prefix, requirement))]
fn pip_install(prefix: &str, requirement: &str) -> PyResult<()> {
    let _ = uv_crate_version();
    let uv_bin = find_uv_executable().map_err(runtime_err)?;
    let status = Command::new(&uv_bin)
        .args(["pip", "install", requirement, "--python", prefix])
        .status()
        .map_err(|e| runtime_err(e.to_string()))?;
    if !status.success() {
        return Err(runtime_err(format!(
            "uv pip install {requirement:?} failed: {status}"
        )));
    }
    Ok(())
}

fn find_uv_executable() -> Result<PathBuf, String> {
    for key in ["ASV_UV_BIN", "UV_BIN"] {
        if let Ok(p) = std::env::var(key) {
            let pb = PathBuf::from(p);
            if pb.is_file() {
                return Ok(pb);
            }
        }
    }
    if let Ok(path) = std::env::var("PATH") {
        for dir in std::env::split_paths(&path) {
            for name in ["uv", "uv.exe"] {
                let cand = dir.join(name);
                if cand.is_file() {
                    return Ok(cand);
                }
            }
        }
    }
    Err("uv executable not found (set ASV_UV_BIN); maturin extension is linked to the uv crate".into())
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_venv, m)?)?;
    m.add_function(wrap_pyfunction!(pip_install, m)?)?;
    m.add_function(wrap_pyfunction!(backend_name, m)?)?;
    m.add_function(wrap_pyfunction!(uv_crate_version, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
