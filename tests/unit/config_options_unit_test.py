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

"""Unit tests for sphinx-config-options extension."""

from unittest.mock import Mock

import pytest
from sphinx_config_options import ConfigOption, parse_option


@pytest.fixture
def mock_directive():
    """Create a mock ConfigOption directive for testing."""
    state = Mock()

    # Mock the document and settings for the env property
    # The env property accesses self.state.document.settings.env
    document = Mock()
    settings = Mock()
    env = Mock()

    # Set up the chain: state.document.settings.env
    state.document = document
    document.settings = settings
    settings.env = env

    # Configure the env mock
    env.docname = "test_doc"
    env.get_domain = Mock()

    # Mock state.nested_parse which is also called during directive execution
    state.nested_parse = Mock()

    directive = ConfigOption(
        name="option",
        arguments=["test_option"],
        options={"shortdesc": "Test option description"},
        content=[],
        lineno=1,
        content_offset=0,
        block_text="",
        state=state,
        state_machine=Mock(),
    )

    # Mock the domain
    domain = Mock()
    domain.add_option = Mock()
    env.get_domain.return_value = domain

    return directive


def test_parse_option():
    """Test the parse_option function."""
    obj = Mock()
    obj.state = Mock()
    obj.state.nested_parse = Mock()

    result = parse_option(obj, "test content")

    assert result is not None
    obj.state.nested_parse.assert_called_once()


def test_config_option_without_shortdesc(mock_directive):
    """Test ConfigOption directive without required shortdesc option."""
    mock_directive.options = {}  # Remove shortdesc

    result = mock_directive.run()

    assert result == []


def test_config_option_with_shortdesc(mock_directive):
    """Test ConfigOption directive with required shortdesc option."""
    result = mock_directive.run()

    # Should return target node and config option node
    assert len(result) == 2

    # Verify domain was called to add the option
    mock_directive.env.get_domain.assert_called_with("config")
    domain = mock_directive.env.get_domain.return_value
    domain.add_option.assert_called_once_with("test_option", "server")


def test_config_option_with_scope(mock_directive):
    """Test ConfigOption directive with custom scope."""
    mock_directive.arguments = ["test_option", "client"]

    result = mock_directive.run()

    # Should return target node and config option node
    assert len(result) == 2

    # Verify domain was called with custom scope
    domain = mock_directive.env.get_domain.return_value
    domain.add_option.assert_called_once_with("test_option", "client")


def test_config_option_optional_fields():
    """Test ConfigOption directive has all expected optional fields."""
    expected_fields = {
        "type",
        "default",
        "defaultdesc",
        "initialvaluedesc",
        "liveupdate",
        "condition",
        "readonly",
        "resource",
        "managed",
        "required",
        "scope",
    }

    actual_fields = set(ConfigOption.optional_fields.keys())

    assert expected_fields == actual_fields
