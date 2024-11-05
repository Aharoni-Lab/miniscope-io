# Installation

From PyPI:

```bash
pip install miniscope_io
```

From git repository, using pip:
```bash
git clone https://github.com/Aharoni-Lab/miniscope-io
cd miniscope-io
pip install .
```

Or pdm:
```bash
git clone https://github.com/Aharoni-Lab/miniscope-io
cd miniscope-io
pdm install
```


## Additional Dependencies

### OpalKelly

`miniscope_io.vendor.opalkelly` - used for FPGA I/O

#### Linux

We package the OpalKelly FrontPanel SDK here, but it has an unadvertised dependency
on some system level packages:

- `liblua5.3-0`

So eg. on debian/ubuntu you'll need to:

```bash
apt install liblua5.3-0
```

#### Mac

No special installation should be required.

#### Windows

Currently windows is not implemented - see `miniscope_io/vencor/opalkelly/README.md` for
what was done to implement Linux and Mac to see what might need to be done here, pull requests welcome :)
