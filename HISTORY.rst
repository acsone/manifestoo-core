1.0 (2023-09-10)
================

Features
--------

- Remove ``setuptools-odoo`` dependency. Let ``metadata_from_addon_dir`` emit Python
  Package Metadata 2.1 (same format, but compatible with PyPI). (`#44 <https://github.com/acsone/manifestoo-core/issues/44>`_)
- Update core addon lists. (`#46 <https://github.com/acsone/manifestoo-core/issues/46>`_)

0.11.0 (2023-03-29)
===================

Features
--------

- Add ``external_dependencies_only`` option to ``metadata_from_addon_dir``, for situations
  where we are interested in the external dependencies only, because dependencies
  on Odoo and other addons are managed in another manner. (`#42 <https://github.com/acsone/manifestoo-core/issues/42>`_)


0.10.6 (2023-03-29)
===================

Features
--------

- Update core addon lists. (`#41 <https://github.com/acsone/manifestoo-core/issues/41>`_)


0.10.5 (2023-03-15)
====================

Features
--------

- Update core addon lists. (`#40 <https://github.com/acsone/manifestoo-core/issues/40>`_)


0.10.4 (2022-12-28)
===================

Features
--------

- Update core addon lists. (`#38 <https://github.com/acsone/manifestoo-core/issues/38>`_)


0.10.3 (2022-11-01)
===================

Features
--------

- Update core addon lists. (`#33 <https://github.com/acsone/manifestoo-core/issues/33>`_)


0.10.2 (2022-10-16)
===================

Features
--------

- Update core addon lists. (`#30 <https://github.com/acsone/manifestoo-core/issues/30>`_)


0.10.1 (2022-09-21)
===================

Features
--------

- Update core addon lists. (`#25 <https://github.com/acsone/manifestoo-core/issues/25>`_, `#27 <https://github.com/acsone/manifestoo-core/issues/27>`_)


0.10 (2022-08-31)
=================

Features
--------

- ``metadata_from_addon_dir``: better detection of invalid addon directories. (`#9 <https://github.com/acsone/manifestoo-core/issues/9>`_)
- Update core addon lists. (`#21 <https://github.com/acsone/manifestoo-core/issues/21>`_)


0.9 (2022-07-08)
================

Features
--------

- New ``is_addon_dir`` function. (`#10 <https://github.com/acsone/manifestoo-core/issues/10>`_)


0.8 (2022-05-26)
================

Features
--------

- Add ``manifestoo_core.metadata.metadata_from_addon_dir`` function to produce
  Python standard package metadata 2.2 from the addon manifest.


0.7 (2022-05-21)
================

Features
--------

- Restore python 3.6 support. (`#7 <https://github.com/acsone/manifestoo-core/issues/7>`_)


0.6 (2022-05-21)
================

Improved Documentation
----------------------

- Document the `core_addons` and `odoo_series` modules. (`#6 <https://github.com/acsone/manifestoo-core/issues/6>`_)


0.5.2 (2022-05-21)
==================

Features
--------

- Update core addon lists. (`#5 <https://github.com/acsone/manifestoo-core/issues/5>`_)

Removals
--------

- Drop python 3.6 support. (`#2 <https://github.com/acsone/manifestoo-core/pull/2>`_)


0.5.0 (2022-05-18)
==================

First release.
