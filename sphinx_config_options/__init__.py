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

from collections import defaultdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Optional

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode
from sphinx.util.typing import ExtensionMetadata

from sphinx_config_options import common

try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("sphinx-config-options")
    except PackageNotFoundError:
        __version__ = "dev"


logger = logging.getLogger(__name__)


def parse_option(obj: ObjectDescription, option: str) -> nodes.inline:
    """Parse rST inside an option field.

    Args:
        obj: The directive object containing parsing state
        option: The option string to parse

    Returns:
        A parsed inline node containing the option content

    """
    new_node = nodes.inline()
    parse_node = ViewList()
    parse_node.append(option, "parsing", 1)
    obj.state.nested_parse(parse_node, 0, new_node)
    return new_node


class ConfigOption(ObjectDescription):
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
            logger.warning(
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
        rows = []

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
        self.state.nested_parse(self.content, self.content_offset, details)

        # Create a new container node with the content
        new_node = nodes.container()
        new_node["classes"].append("configoption")
        new_node += first_line
        new_node += details

        # Register the target with the domain
        config_domain = self.env.get_domain("config")
        config_domain.add_option(self.arguments[0], scope)

        # Return the content and target node
        return [target_node, new_node]


class ConfigIndex(Index):
    """Index for configuration options."""

    # To link to the index: {ref}`config-options`
    name = "options"
    localname = "Configuration options"

    def generate(
        self, _docnames: list[str] | None = None
    ) -> tuple[list[tuple[str, list[Any]]], bool]:
        """Generate the index content."""
        content: dict[str, list[Any]] = defaultdict(list)

        options = self.domain.get_objects()
        # sort by key name
        options = sorted(options, key=lambda option: (option[1], option[4]))

        dispnames = []
        duplicates = []
        for _name, dispname, _typ, _docname, anchor, _priority in options:
            fullname = anchor.partition(":")[0].partition("-")[0] + "-" + dispname
            if fullname in dispnames:
                duplicates.append(fullname)
            else:
                dispnames.append(fullname)

        for _name, dispname, _typ, docname, anchor, _priority in options:
            scope = anchor.partition(":")[0].partition("-")

            # if the key exists more than once within the scope, add
            # the title of the document as extra context
            if scope[0] + "-" + dispname in duplicates:
                extra = str(self.domain.env.titles[docname])
                # need some tweaking to work with our CSS
                extra = extra.replace("<title>", "")
                extra = extra.replace("</title>", "")
                extra = extra.replace("<literal>", '<code class="literal">')
                extra = extra.replace("</literal>", "</code>")
                # add the anchor for full information
                extra += f': <code class="literal">{scope[2]}</code>'
            else:
                extra = ""

            # group by the first part of the scope
            # ("XXX" if the scope is "XXX-YYY")
            content[scope[0]].append((dispname, 0, docname, anchor, extra, "", ""))

        return sorted(content.items()), True


class ConfigDomain(Domain):
    """Domain for configuration options."""

    name = "config"
    label = "Configuration Options"
    roles = {"option": XRefRole()}
    directives = {"option": ConfigOption}
    indices = {ConfigIndex}
    initial_data = {"config_options": []}

    def get_objects(self) -> list[tuple[str, str, str, str, str, int]]:
        """Return an iterable of tuples describing the objects in this domain."""
        yield from self.data["config_options"]

    def resolve_xref(
        self,
        _env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        _typ: str,
        target: str,
        _node: nodes.Element,
        _contnode: nodes.Element,
    ) -> nodes.Element | None:
        """Find the node that is being referenced."""
        # If the scope isn't specified, default to "server"
        if ":" not in target:
            target = f"server:{target}"

        matches = [
            (key, docname, anchor)
            for key, sig, typ_match, docname, anchor, prio in self.get_objects()
            if anchor == target and typ_match == "option"
        ]

        if matches:
            title = matches[0][0]
            todocname = matches[0][1]
            targ = matches[0][2]

            refnode = make_refnode(
                builder,
                fromdocname,
                todocname,
                targ,
                child=nodes.literal(text=title),
            )
            refnode["classes"].append("configref")
            return refnode
        logger.warning(f"Could not find target {target} in {fromdocname}")
        return None

    def resolve_any_xref(
        self,
        _env: BuildEnvironment,
        _fromdocname: str,
        _builder: Builder,
        _target: str,
        _node: nodes.Element,
        _contnode: nodes.Element,
    ) -> list[tuple[str, nodes.Element]]:
        """We don't want to link with "any" role, but only with "config:option"."""
        return []

    def add_option(self, key: str, scope: str) -> None:
        """Store the option in the domain data."""
        self.data["config_options"].append(
            (key, key, "option", self.env.docname, f"{scope}:{key}", 0)
        )

    def merge_domaindata(self, _docnames: list[str], otherdata: dict[str, Any]) -> None:
        """Merge domain data from multiple processes."""
        for option in otherdata["config_options"]:
            if option not in self.data["config_options"]:
                self.data["config_options"].append(option)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up the sphinx-config-options extension."""
    app.add_domain(ConfigDomain)

    common.add_css(app, "config-options.css")
    common.add_js(app, "config-options.js")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


__all__ = ["__version__", "setup"]
