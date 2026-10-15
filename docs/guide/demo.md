# Demo

Minimal functionality checks on the small sample data in `tests/data`.
Run from a clone of the repository after installing with `pip install .[plot]`.
Each takes a few seconds on a normal desktop computer.

## Streaming

Decode a raw FPGA capture through the mock device:

```bash
mio stream test \
  -c tests/data/config/stream_daq_test_200px.yml \
  -s tests/data/stream_daq_test_fpga_raw_input_200px.bin \
  -o demo_stream \
  --no-display
```

Expected output: `demo_stream.avi` (video) and `demo_stream.csv` (frame metadata).

## Processing

Stitch and denoise two sample recordings:

```bash
mio process workflow \
  -i tests/data/stitch/video1.avi \
  -i tests/data/stitch/video2.avi \
  -o demo_out \
  -c denoise_example
```

Expected output: `demo_out/video1__video2_stitched.avi` (stitched video),
`demo_out/user_data/output/video1__video2_stitched_patch.avi` (denoised video),
and accompanying `.csv` metadata.

## Tests

```bash
pip install .[tests]
pytest
```

All tests should pass within a few minutes on a normal desktop computer.
