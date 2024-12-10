# OpalKelly FPGA SDK

See documentation here: https://docs.opalkelly.com/fpsdk/frontpanel-api/programming-languages/

## Files

The Python API distribution includes the files listed below:

- `ok.py`
- `_ok.pyd` – Windows, architecture-specific for 32-bit/64-bit
- `_ok.so` – Linux, Mac OS, architecture-specific for 32-bit/64-bit
- `okFrontPanel.dll` – Windows, architecture-specific for 32-bit/64-bit
- `libokFrontPanel.so` – Linux, Mac OS, architecture-specific for 32-bit/64-bit
- `okimpl_fpoip.dll` – (optional) Windows, architecture-specifc DLL used to provide FPoIP functionality
- `okimpl_fpoip.so` – (optional) Linux, architecture-specifc DLL used to provide FPoIP functionality

## Changes

### Mac

The documentation suggests that all one needs to do is add the folders to
`DYLD_LIBRARY_PATH`, but unfortunately that doesn't work because they have hard-coded
the location to search for the dylib as `@rpath/libokFrontPanel.dylib` and 
then set `rpath` to some weird directory on their build server.

So instead we modify the import location in `_ok.so` like:

```bash
install_name_tool -change \
  @rpath/libokFrontPanel.dylib \
  @loader_path/libokFrontPanel.dylib \
  mio/vendor/opalkelly/mac/_ok.so
```

### Linux

Since we can't modify `LD_LIBRARY_PATH` dynamically, we change the location
of the loaded `libokFrontPanel.so` to be `$ORIGIN/libokFrontPanel.so`

```bash
patchelf --remove-needed libokFrontPanel.so mio/vendor/opalkelly/linux/_ok.so
patchelf --add-needed '$ORIGIN/libokFrontPanel.so' mio/vendor/opalkelly/linux/_ok.so
```

We also need to install `liblua5.3-0` (`apt install liblua5.3-0`)!