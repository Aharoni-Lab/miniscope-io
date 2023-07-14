# Changelog

## 0.1.1 - 23-07-13

### Additions

- Added {class}`~miniscope_io.exceptions.EndOfRecordingException` when attempting to read past last frame
- Added {attr}`~miniscope_io.io.SDCard.frame_count` property inferred from the number of buffers and buffers per frame
- Return `self` when entering {class}`~.SDCard` context
- Optionally return {class}`~miniscope_io.sd.DataHeader`s from frame when reading

### Bugfixes

- Index the position of the 0th frame in {attr}`~.SDCard.positions`
- reset internal frame counter to 0 when exiting context