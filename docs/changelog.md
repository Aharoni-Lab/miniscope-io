# Changelog

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