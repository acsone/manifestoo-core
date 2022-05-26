# API Reference

## `manifestoo_core.core_addons`

```{eval-rst}
.. automodule:: manifestoo_core.core_addons
   :members:
```

## `manifestoo_core.exceptions`

```{eval-rst}
.. automodule:: manifestoo_core.exceptions
   :members:
   :undoc-members:
```

## `manifestoo_core.metadata`

```{note}
For this module to be functional, `manifestoo-core` must currently be installed
with the `metadata` extra (`pip install manifestoo-core[metadata]`) because it pulls
`setuptools-odoo` as a dependency to implement this functionality. In the future,
this feature will be implemented natively as part of `manifestoo-core` and the extra
will become unnecessary.
```

```{eval-rst}
.. automodule:: manifestoo_core.metadata
   :members:
```

## `manifestoo_core.odoo_series`

```{eval-rst}
.. automodule:: manifestoo_core.odoo_series
   :members:
   :exclude-members: OdooSeries, OdooEdition

   .. autoclass:: manifestoo_core.odoo_series.OdooSeries
      :members:
      :undoc-members:

   .. autoclass:: manifestoo_core.odoo_series.OdooEdition
      :members:
      :undoc-members:
```
