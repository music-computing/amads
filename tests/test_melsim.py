import os

import pytest

from amads.melody.similarity.melsim import check_r_packages_installed


@pytest.fixture(scope="session")
def installed_melsim_dependencies():
    on_ci = os.environ.get("CI") is not None
    install_missing = on_ci
    check_r_packages_installed(install_missing=install_missing)


def test_melsim_import(installed_melsim_dependencies):
    """Test that melsim can be imported."""
    from amads.melody.similarity.melsim import get_similarity

    assert callable(get_similarity)
