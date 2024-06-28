"""
Directly call miniscope-io cli from python module rather than entrypoint script `mio`
"""

from miniscope_io.cli.main import cli

if __name__ == "__main__":
    cli()
