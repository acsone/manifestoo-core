v1.6 (2024-05-20)
=================

Features
--------

- Update core addon lists. (`#71 <https://github.com/acsone/manifestoo-core/issues/71>`_)


v1.5 (2024-03-16)
=================

Features
--------

- Update core addon lists. (`#67 <https://github.com/acsone/manifestoo-core/issues/67>`_)


v1.4 (2023-12-22)
=================

Features
--------

- Update core addon lists. (`#60 <https://github.com/acsone/manifestoo-core/issues/60>`_, `#65 <https://github.com/acsone/manifestoo-core/issues/65>`_)


Bugfixes
--------

- Fix metadata generation for addons containing upper case letters in their name. (`#63 <https://github.com/acsone/manifestoo-core/issues/63>`_)


v1.3 (2023-10-30)
=================

Features
--------

- Add the ``category`` field to ``Manifest``. (`#57 <https://github.com/acsone/manifestoo-core/issues/57>`_)
- Document the ``Addon`` and ``Manifest`` classes and assorted methods. (`#58 <https://github.com/acsone/manifestoo-core/issues/58>`_)


v1.2 (2023-10-29)
=================

Features
--------

- Initial support for Odoo 17. (`#56 <https://github.com/acsone/manifestoo-core/issues/56>`_)


v1.1 (2023-10-21)
=================

Features
--------

- Renamed ``UnsupportedOdooVersion`` exception to ``UnsupportedOdooSeries``.
  ``UnsupportedOdooVersion`` is preserved as a compatibility alias. (`#50 <https://github.com/acsone/manifestoo-core/issues/50>`_)
- Add functions to convert addon names to and from distribution names and requirements
  (including the Odoo version specifier): ``addon_name_to_distribution_name``,
  ``addon_name_to_requirement`` and ``distribution_name_to_addon_name``. (`#52 <https://github.com/acsone/manifestoo-core/issues/52>`_)
- Add support for ``odoo_series_override`` metadata option, as a preferred alias to
  ``odoo_version_override``. (`#53 <https://github.com/acsone/manifestoo-core/issues/53>`_)
- Update core addon lists. (`#55 <https://github.com/acsone/manifestoo-core/issues/55>`_)


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
