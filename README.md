# sphinx-config-options

sphinx-config-options adds functionality to Sphinx that allows documenting configuration options with rich metadata and cross-referencing capabilities.

## Basic usage

### Documenting configuration options

Add configuration options to your documentation using the `config:option` directive:

```rst
.. config:option:: database.host
   :shortdesc: Database hostname or IP address
   :type: string
   :default: localhost
   :required: true

   The hostname or IP address of the database server to connect to.
```

### Advanced option fields

The extension supports various metadata fields:

```rst
.. config:option:: cache.enabled
   :shortdesc: Enable or disable caching
   :type: boolean
   :default: false
   :scope: server
   :liveupdate: true
   :condition: Only available with premium license

   Controls whether the application uses caching to improve performance.
```

### Cross-referencing options

Reference configuration options from anywhere in your documentation:

```rst
See the :config:option:`database.host` option for connection details.
```

### Automatic index generation

All documented configuration options are automatically added to a searchable index available at `{ref}config-options`.

## Project setup

sphinx-config-options is published on PyPI and can be installed with:

```bash
pip install sphinx-config-options
```

After adding sphinx-config-options to your Python project, update your Sphinx's conf.py file to include sphinx-config-options as one of its extensions:

```python
extensions = [
    "sphinx_config_options"
]
```

## Supported option fields

The extension supports the following metadata fields for configuration options:

- `shortdesc` (required): Brief description of the option
- `type`: Data type (string, boolean, integer, etc.)
- `default`: Default value
- `defaultdesc`: Description of the default value
- `initialvaluedesc`: Description of the initial value
- `liveupdate`: Whether the option can be changed at runtime
- `condition`: Conditions under which the option is available
- `readonly`: Whether the option is read-only
- `resource`: Resource associated with the option
- `managed`: Whether the option is managed by the system
- `required`: Whether the option is required
- `scope`: Scope of the option (server, client, etc.)

For more examples, see:
https://linuxcontainers.org/lxd/docs/latest/networks/config_options_cheat_sheet.

## Community and support

You can report any issues or bugs on the project's [GitHub repository](https://github.com/canonical/sphinx-config-options).

sphinx-config-options is covered by the [Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct).

## License and copyright

sphinx-config-options is released under the [GPL-3.0 license](LICENSE).

© 2025 Canonical Ltd.
