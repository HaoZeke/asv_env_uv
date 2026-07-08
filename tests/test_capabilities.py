# Licensed under a 3-clause BSD style license - see LICENSE.rst
from asv_env_uv import Uv


def test_capability_attrs():
    assert Uv.matrix_install_mode == 'create'
    assert Uv.supports_joint_pypi_solve is True
    assert Uv.project_install_prefers_no_deps is True

