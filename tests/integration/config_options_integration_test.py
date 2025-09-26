# This file is part of sphinx-config-options.
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Integration tests for sphinx-config-options extension."""

import shutil
import subprocess
import sys
from pathlib import Path

import bs4
import pytest

# Add the extension to the path
sys.path.insert(0, str(Path(__file__).parents[2] / "sphinx_config_options"))


def test_extension_can_be_imported():
    """Test that the extension can be imported without errors."""
    try:
        import sphinx_config_options

        assert hasattr(sphinx_config_options, "setup")
        assert callable(sphinx_config_options.setup)
    except ImportError as e:
        pytest.fail(f"Failed to import sphinx_config_options: {e}")


def test_extension_setup_function():
    """Test that the setup function returns correct metadata."""
    from unittest.mock import Mock, patch

    import sphinx_config_options

    app_mock = Mock()
    app_mock.add_domain = Mock()

    with patch("sphinx_config_options.common.add_css") as mock_add_css:
        with patch("sphinx_config_options.common.add_js") as mock_add_js:
            result = sphinx_config_options.setup(app_mock)

    assert "version" in result
    assert "parallel_read_safe" in result
    assert "parallel_write_safe" in result
    assert result["parallel_read_safe"] is True
    assert result["parallel_write_safe"] is True


@pytest.fixture
def example_project(request) -> Path:
    """Create a temporary example project for testing."""
    project_root = request.config.rootpath
    example_dir = project_root / "tests/integration/example"

    # Copy the project into the test's own temporary dir, to avoid clobbering
    # the sources.
    target_dir = Path().resolve() / "example"
    shutil.copytree(example_dir, target_dir, dirs_exist_ok=True)

    return target_dir


@pytest.mark.slow
def test_config_options_integration(example_project):
    """Test that the config options extension builds correctly."""
    build_dir = example_project / "_build"
    subprocess.check_call(
        ["sphinx-build", "-b", "html", "-W", example_project, build_dir],
    )

    index = build_dir / "index.html"

    # Rename the test output to something more meaningful
    shutil.copytree(
        build_dir, build_dir.parents[1] / ".test_output", dirs_exist_ok=True
    )

    soup = bs4.BeautifulSoup(index.read_text(), features="lxml")
    shutil.rmtree(example_project)  # Delete copied source

    # Check that config option elements exist
    config_option = soup.find(class_="configoption")
    if not config_option:
        pytest.fail("Config option directive output not found in document.")

    # Check that the option key is present
    key_element = config_option.find(class_="key")
    if not key_element:
        pytest.fail("Config option key not found in output.")

    # Check that CSS was included
    css_links = soup.find_all("link", {"rel": "stylesheet"})
    css_hrefs = [link.get("href") for link in css_links]
    assert any("config-options.css" in href for href in css_hrefs), (
        "CSS file not included"
    )
