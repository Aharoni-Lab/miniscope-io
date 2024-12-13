"""
Directly call mio cli from python module rather than entrypoint script `mio`
"""

from mio.cli.main import cli

if __name__ == "__main__":
    cli()
