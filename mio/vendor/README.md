# Vendor module

The vendor module contains unmodified source code
and binaries from non-free or non-open sources.

* To avoid making derivative works, code in vendored modules should
  remain unchanged.
* This module should be imported from sparingly - since in the
  future we may need to remove some of these pieces and make
  them optional components, imports should be limited to
  only the modules that directly make use of them
* When adding new vendor modules, add the appropriate
  `LICENSE` file that explains the terms of its use.