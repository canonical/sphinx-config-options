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

"""Contains the custom domain for sphinx-config-options."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from docutils import nodes
from sphinx.builders import Builder
from sphinx.domains import Domain, Index
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode
from typing_extensions import override

from sphinx_config_options.directive import ConfigOption

Logger = logging.getLogger(__name__)


class ConfigIndex(Index):
    """Index for the ConfigDomain."""

    # To link to the index: {ref}`config-options`
    name = "options"
    localname = "Configuration options"

    @override
    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[Any]]], bool]:
        """Generate the index content."""
        content: dict[str, list[Any]] = defaultdict(list)

        options = self.domain.get_objects()
        # sort by key name
        options = sorted(options, key=lambda option: (option[1], option[4]))

        dispnames: list[str] = []
        duplicates: list[str] = []
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
    indices = [ConfigIndex]
    initial_data: dict[str, list[str]] = {"config_options": []}

    @override
    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        """Return an iterable of tuples describing the objects in this domain."""
        yield from self.data["config_options"]

    @override
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: nodes.Element,
        contnode: nodes.Element,
    ) -> nodes.Element | None:
        """Find the node that is being referenced."""
        # If the scope isn't specified, default to "server"
        if ":" not in target:
            target = f"server:{target}"

        matches = [
            (key, docname, anchor)
            for key, _, typ_match, docname, anchor, _ in self.get_objects()
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
        Logger.warning(f"Could not find target {target} in {fromdocname}")
        return None

    @override
    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: nodes.Element,
        contnode: nodes.Element,
    ) -> list[tuple[str, nodes.Element]]:
        """We don't want to link with "any" role, but only with "config:option"."""
        return []

    @override
    def merge_domaindata(self, docnames: list[str], otherdata: dict[str, Any]) -> None:
        """Merge domain data from multiple processes."""
        for option in otherdata["config_options"]:
            if option not in self.data["config_options"]:
                self.data["config_options"].append(option)
