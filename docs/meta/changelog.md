# Changelog

## 0.2

### 0.2.1 - 24-06-21

Linting and code formatting :)

Added `black` and `ruff` for linting and formatting, 
reformatted the package.

See the [Contributing](./contributing.md) documentation for 
details and usage.

### 0.2.0 - 24-06-21

StreamDaq enhancements and testing

- https://github.com/Aharoni-Lab/miniscope-io/pull/26

Testing:

- [@t-sasatani](https://github.com/t-sasatani) - add end-to-end test for {class}`~miniscope_io.stream_daq.streamDaq`
- Add a mock class for {class}`~miniscope_io.devices.opalkelly.okDev`
- replace `tmpdir` fixture and `tempfile` module with `tmp_path`

New:

- [@t-sasatani](https://github.com/t-sasatani) - allow use of okDev on Windows
- {meth}`~miniscope_io.stream_daq.StreamDaq.capture` can export video :)
- More specific exceptions:
  - {class}`~miniscope_io.exceptions.StreamError`
  - {class}`~miniscope_io.exceptions.StreamReadError`
  - {class}`~miniscope_io.exceptions.DeviceError`
  - {class}`~miniscope_io.exceptions.DeviceOpenError`
  - {class}`~miniscope_io.exceptions.DeviceConfigurationError`
- {func}`~miniscope_io.utils.hash_video` - hash decoded video frames, rather than encoded video file


Fixed:

- Removed `print` statements in {class}`~miniscope_io.devices.opalkelly.okDev`
- {meth}`~miniscope_io.stream_daq.StreamDaq.capture`
  - Don't require `config`
  - Replace logging with {func}`~miniscope_io.logging.init_logger`
  - Use of {attr}`~miniscope_io.stream_daq.StreamDaq.terminate` to control inner loops


Models:

- added `fs` and `show_video` to {class}`~miniscope_io.models.stream.StreamDaqConfig`

CI:

- [@t-sasatani](https://github.com/t-sasatani) - restore windows and mac tests (oops)
- caching dependency installs
- not using pytest-emoji, it was always annoying

## 0.1

### 0.1.8 - 24-06-16

- https://github.com/Aharoni-Lab/miniscope-io/pull/21
- https://github.com/Aharoni-Lab/miniscope-io/pull/15

New features:

- **Support for Various Image Formats**: `streamDaq` now supports multiple image formats, including different image sizes, frame rates (FPS), and bit-depths. These configurations can be provided via a YAML file. Examples of these configurations can be found in `miniscope_io.data.config`.
- **Pydantic Model for Configuration**: Added a Pydantic model to validate the configuration of `streamDaq`.
- **Bitstream Loader**: Added a bitstream loader to automatically configure the Opal Kelly FPGA when running `streamDaq`.
- **Updated Command Line Script**: The command line script for running `streamDaq` has been updated. Use `streamDaq -c path/to/config/yaml/file.yml` to run the process with your YAML configuration file.
- **Logger Module**: Added a logger module that can be configured using environmental variables or a `.env` file.

Note: Version 0.1.7 was skipped accidentally and does not exist.

### 0.1.6 - 24-04-09

- https://github.com/Aharoni-Lab/miniscope-io/pull/14

New features:

- Added support for the wireless FPGA and UART daqs - work in progress unifying the API, but
  initial version of code is present in `stream_daq.py`
- Vendored opalkelly device drivers - see `devices` and `vendor`

### 0.1.5 - 23-09-03

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

### 0.1.4 - 23-09-03

https://github.com/Aharoni-Lab/miniscope-io/pull/8

New features:

- Data models! Hold a collection of frames and get their headers
- Plots! Mimic the plots from ye olde notebook
- Update to pydantic v2
- Version field in formats
- Format for miniscope firmware with battery voltage level

Reverted:

- grab_frames notebook is restored to using the example data and having the evaluated output present



### 0.1.1 - 23-07-13

#### Additions

- Added {class}`~miniscope_io.exceptions.EndOfRecordingException` when attempting to read past last frame
- Added {attr}`~miniscope_io.io.SDCard.frame_count` property inferred from the number of buffers and buffers per frame
- Return `self` when entering {class}`~.SDCard` context
- Optionally return {class}`~miniscope_io.sd.DataHeader`s from frame when reading

#### Bugfixes

- Index the position of the 0th frame in {attr}`~.SDCard.positions`
- reset internal frame counter to 0 when exiting context