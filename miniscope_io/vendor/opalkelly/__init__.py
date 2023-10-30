import pdb
import sys
from pathlib import Path
import os
import subprocess
import pdb


def patch_env_path(name:str, value:str):
    val = os.environ.get(name, None)
    if val is None:
        val = value
    else:
        val = ':'.join([val.rstrip(':'), value])
    os.environ[name] = val

base_path = Path(__file__).parent.resolve()
if sys.platform == 'darwin':
    from miniscope_io.vendor.opalkelly.mac.ok import *

elif sys.platform.startswith('linux'):
    # Linux
    from miniscope_io.vendor.opalkelly.linux.ok import *

elif sys.platform.startswith('win'):
    # Windows
    pass
else:
    raise ImportError('Dont know what operating system you are on, cant use OpalKelly')
