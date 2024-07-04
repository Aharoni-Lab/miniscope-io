"""
Miniscope-io ``mio`` CLI interface.

.. note::

    Currently commands are organized by device, as in `mio streamdaq capture` ,
    but as the API matures will be refactored by action - `mio capture streamdaq` .

    Each entrypoint is a bit too heterogeneous to make that work for now, but
    the design goal here is to be able to use the same command syntax across any
    device.

Structure:
- Define commands per module - each module should correspond to a command, and further
  levels of nesting should either create nested packages or nested naming structure
- Import each top-level command into `main` and use `add_command` to combine them
- Try and keep arguments grouped in decorator groups (see ``stream._capture_options`` )
  for DRY rather than forwarding parameters through nested groups/commands
"""
