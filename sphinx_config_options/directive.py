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

"""Contains the core elements of the sphinx-config-options extension."""

from typing import TypeVar

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.directives import ObjectDescription
from sphinx.util import logging

Logger = logging.getLogger(__name__)
ObjDescT = TypeVar("ObjDescT")


def parse_option(obj: ObjectDescription[ObjDescT], option: str) -> nodes.inline:
    """Parse rST inside an option field.

    Args:
        obj: The directive object containing parsing state
        option: The option string to parse

    Returns:
        A parsed inline node containing the option content

    """
    new_node = nodes.inline()
    parse_node: ViewList[str] = ViewList()
    parse_node.append(option, "parsing", 1)
    obj.state.nested_parse(parse_node, 0, new_node)  # type: ignore[arg-type,reportUnknownMemberType]
    return new_node


class ConfigOption(ObjectDescription[ObjDescT]):
    """Directive for documenting configuration options."""

    optional_fields = {
        "type": "Type",
        "default": "Default",
        "defaultdesc": "Default",
        "initialvaluedesc": "Initial value",
        "liveupdate": "Live update",
        "condition": "Condition",
        "readonly": "Read-only",
        "resource": "Resource",
        "managed": "Managed",
        "required": "Required",
        "scope": "Scope",
    }

    required_arguments = 1
    optional_arguments = 1
    has_content = True
    option_spec = {
        "shortdesc": directives.unchanged_required,
        "type": directives.unchanged,
        "default": directives.unchanged,
        "defaultdesc": directives.unchanged,
        "initialvaluedesc": directives.unchanged,
        "liveupdate": directives.unchanged,
        "condition": directives.unchanged,
        "readonly": directives.unchanged,
        "resource": directives.unchanged,
        "managed": directives.unchanged,
        "required": directives.unchanged,
        "scope": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:  # noqa: PLR0915
        """Execute the directive and return the generated nodes."""
        # Create a target ID and target
        scope = "server"
        if len(self.arguments) > 1:
            scope = self.arguments[1]
        target_id = f"{scope}:{self.arguments[0]}"
        target_node = nodes.target("", "", ids=[target_id])

        # Generate the output
        key = nodes.inline()
        key += nodes.literal(text=self.arguments[0])
        key["classes"].append("key")

        if "shortdesc" not in self.options:
            Logger.warning(
                f"The option fields for the {self.arguments[0]} option could not be parsed. "
                "No output was generated."
            )
            return []

        short_desc = parse_option(self, self.options["shortdesc"])
        short_desc["classes"].append("shortdesc")

        anchor = nodes.inline()
        anchor["classes"].append("anchor")
        refnode = nodes.reference("", refuri=f"#{target_id}")
        refnode += nodes.raw(
            text='<i class="icon"><svg><use href="#svg-arrow-right"></use></svg></i>',
            format="html",
        )
        anchor += refnode

        first_line = nodes.container()
        first_line["classes"].append("basicinfo")
        first_line += key
        first_line += short_desc
        first_line += anchor

        details = nodes.container()
        details["classes"].append("details")
        fields = nodes.table()
        fields["classes"].append("fields")
        tgroup = nodes.tgroup(cols=2)
        fields += tgroup
        tgroup += nodes.colspec(colwidth=1)
        tgroup += nodes.colspec(colwidth=3)
        rows: list[nodes.row] = []

        # Add the key name again
        row_node = nodes.row()
        desc_entry = nodes.entry()
        desc_entry += nodes.strong(text="Key: ")
        val_entry = nodes.entry()
        val_entry += nodes.literal(text=self.arguments[0])
        row_node += desc_entry
        row_node += val_entry
        rows.append(row_node)

        # Add the other fields
        for field in self.optional_fields:
            if field in self.options:
                row_node = nodes.row()
                desc_entry = nodes.entry()
                desc_entry += nodes.strong(text=f"{self.optional_fields[field]}: ")
                parsed_option = parse_option(self, self.options[field])
                parsed_option["classes"].append("ignoreP")
                val_entry = nodes.entry()
                val_entry += parsed_option
                row_node += desc_entry
                row_node += val_entry
                rows.append(row_node)

        tbody = nodes.tbody()
        tbody.extend(rows)
        tgroup += tbody
        details += fields
        self.state.nested_parse(self.content, self.content_offset, details)  # type: ignore[reportUnknownMemberType]

        # Create a new container node with the content
        new_node = nodes.container()
        new_node["classes"].append("configoption")
        new_node += first_line
        new_node += details

        # Register the target with the domain
        config_domain = self.env.get_domain("config")
        config_domain.data["config_options"].append(
            (
                self.arguments[0],
                self.arguments[0],
                "option",
                config_domain.env.docname,
                f"{scope}:{self.arguments[0]}",
                0,
            )
        )

        # Return the content and target node
        return [target_node, new_node]
