import sys
from pathlib import Path
import os


def patch_env_path(name: str, value: str):
    val = os.environ.get(name, None)
    if val is None:
        val = value
    else:
        val = ":".join([val.rstrip(":"), value])
    os.environ[name] = val


base_path = Path(__file__).parent.resolve()

if sys.platform == "darwin":
    from mio.vendor.opalkelly.mac.ok import *

elif sys.platform.startswith("linux"):
    # Linux
    from mio.vendor.opalkelly.linux.ok import *

elif sys.platform.startswith("win"):
    from mio.vendor.opalkelly.win.ok import *
else:
    raise ImportError("Dont know what operating system you are on, cant use OpalKelly")
