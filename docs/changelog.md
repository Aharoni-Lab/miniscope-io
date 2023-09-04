# Changelog

## 0.1.5 - 23-09-03

- https://github.com/Aharoni-Lab/miniscope-io/pull/9
- https://github.com/Aharoni-Lab/miniscope-io/pull/10

Bugfixes:
- Handle absolute paths correctly on windows, which can't deal with {meth}`pathlib.Path.resolve()`, apparently

New features:
- Added {meth}`~miniscope_io.io.SDCard.to_video` to export videos
  - Added notebook demonstrating {meth}`~miniscope_io.io.SDCard.to_video`
- Added {mod}`miniscope_io.utils` module with {func}`~.utils.hash_file` function for hashing files (used in testing)

Code structure:
- (Minor) moved {meth}`~miniscope_io.io.SDCard.skip` to general methods block (no change)

Tests:
- Run tests on macos and windows

## 0.1.4 - 23-09-03

https://github.com/Aharoni-Lab/miniscope-io/pull/8

New features:

- Data models! Hold a collection of frames and get their headers
- Plots! Mimic the plots from ye olde notebook
- Update to pydantic v2
- Version field in formats
- Format for miniscope firmware with battery voltage level

Reverted:

- grab_frames notebook is restored to using the example data and having the evaluated output present



## 0.1.1 - 23-07-13

### Additions

- Added {class}`~miniscope_io.exceptions.EndOfRecordingException` when attempting to read past last frame
- Added {attr}`~miniscope_io.io.SDCard.frame_count` property inferred from the number of buffers and buffers per frame
- Return `self` when entering {class}`~.SDCard` context
- Optionally return {class}`~miniscope_io.sd.DataHeader`s from frame when reading

### Bugfixes

- Index the position of the 0th frame in {attr}`~.SDCard.positions`
- reset internal frame counter to 0 when exiting context