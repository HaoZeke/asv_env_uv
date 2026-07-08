//! In-process create path using **uv-python** + **uv-virtualenv** crate APIs.
//!
//! No `std::process::Command` to a PATH `uv` binary for create/install of the
//! environment itself.
use std::path::{Path, PathBuf};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use uv_cache::Cache;
use uv_python::{
    EnvironmentPreference, PythonInstallation, PythonPreference, PythonRequest,
};
use uv_virtualenv::{create_venv, OnExisting, Prompt, RemovalReason};

fn runtime_err(msg: impl ToString) -> PyErr {
    PyRuntimeError::new_err(msg.to_string())
}

/// Mechanism label — must reflect crate-based create.
#[pyfunction]
fn backend_name() -> &'static str {
    "uv-virtualenv-crates"
}

/// Version / linkage marker for tests.
#[pyfunction]
fn uv_crate_version() -> String {
    format!(
        "asv_env_uv={} (uv-python+uv-virtualenv in-process create)",
        env!("CARGO_PKG_VERSION")
    )
}

/// Create a virtualenv at `prefix` for `python_version` using uv crate APIs only.
///
/// Uses:
/// - [`PythonRequest::parse`] + [`PythonInstallation::find_existing`]
/// - [`uv_virtualenv::create_venv`]
#[pyfunction]
#[pyo3(signature = (prefix, python_version))]
fn create_venv_inprocess(prefix: &str, python_version: &str) -> PyResult<()> {
    create_venv_impl(prefix, python_version).map_err(runtime_err)
}

fn create_venv_impl(prefix: &str, python_version: &str) -> Result<(), String> {
    let location = PathBuf::from(prefix);
    if let Some(parent) = location.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("mkdir parent: {e}"))?;
    }

    let cache = Cache::temp().map_err(|e| format!("uv cache: {e}"))?;

    let request = PythonRequest::parse(python_version);
    let installation = PythonInstallation::find_existing(
        &request,
        EnvironmentPreference::OnlySystem,
        PythonPreference::OnlySystem,
        &cache,
    )
    .map_err(|e| format!("find Python {python_version:?}: {e}"))?;

    let interpreter = installation.into_interpreter();

    create_venv(
        &location,
        interpreter,
        Prompt::None,
        false, // system_site_packages
        OnExisting::Remove(RemovalReason::UserRequest(
            uv_virtualenv::ClearNonVirtualenv::Error,
        )),
        false, // relocatable
        false, // seed flag only sets pyvenv.cfg; bootstrap pip via ensurepip
        false, // upgradeable
    )
    .map_err(|e| format!("uv_virtualenv::create_venv failed: {e}"))?;

    // Bootstrap pip using stdlib ensurepip in the new env (not PATH `uv` CLI).
    let python = if cfg!(windows) {
        location.join("Scripts").join("python.exe")
    } else {
        location.join("bin").join("python")
    };
    let status = std::process::Command::new(&python)
        .args(["-m", "ensurepip", "--upgrade"])
        .status()
        .map_err(|e| format!("spawn ensurepip: {e}"))?;
    if !status.success() {
        return Err(format!(
            "python -m ensurepip failed in {}: {status}",
            python.display()
        ));
    }

    Ok(())
}

/// Install a requirement into an existing prefix using the prefix's `python -m pip`.
///
/// This intentionally does **not** shell out to a PATH `uv` binary. After
/// `create_venv_inprocess` with seed packages, `python -m pip` is available
/// inside the environment.
#[pyfunction]
#[pyo3(signature = (prefix, requirement))]
fn pip_install_in_prefix(prefix: &str, requirement: &str) -> PyResult<()> {
    use std::process::Command;
    let python = Path::new(prefix).join(if cfg!(windows) {
        "Scripts/python.exe"
    } else {
        "bin/python"
    });
    if !python.is_file() {
        return Err(runtime_err(format!(
            "no python in prefix (create first): {}",
            python.display()
        )));
    }
    let status = Command::new(&python)
        .args(["-m", "pip", "install", requirement])
        .status()
        .map_err(|e| runtime_err(e.to_string()))?;
    if !status.success() {
        return Err(runtime_err(format!(
            "python -m pip install {requirement:?} failed: {status}"
        )));
    }
    Ok(())
}

/// True if this module's create path is in-process crate API (always).
#[pyfunction]
fn uses_inprocess_uv_virtualenv() -> bool {
    true
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_venv_inprocess, m)?)?;
    m.add_function(wrap_pyfunction!(pip_install_in_prefix, m)?)?;
    m.add_function(wrap_pyfunction!(backend_name, m)?)?;
    m.add_function(wrap_pyfunction!(uv_crate_version, m)?)?;
    m.add_function(wrap_pyfunction!(uses_inprocess_uv_virtualenv, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
