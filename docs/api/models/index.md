# models

Pydantic models used throughout `miniscope_io`.

These models should be kept as generic as possible, and any refinements
needed for a specific acquisition class should be defined within that
module, inheriting from the relevant parent class. Rule of thumb: 
keep what is common common, and what is unique unique.



```{eval-rst}
.. automodule:: miniscope_io.models
    :members:
    :undoc-members:
```

```{toctree}
buffer
config
data
mixins
models
sdcard
stream
```