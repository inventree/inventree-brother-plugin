# inventree-brother-plugin

A label printing plugin for [InvenTree](https://inventree.org), which provides support for the [Brother label printers](https://www.brother.com.au/en/products/all-labellers/labellers).

This plugin supports printing to *some* Brother label printers with network (wired or WiFi) support. Refer to the [brother_ql docs](https://github.com/pklaus/brother_ql/blob/master/brother_ql/models.py) for a list of label printers which are directly supported.

## Installation

This plugin is available on [pypi]() and can be installed via PIP with the following command:

```
pip install inventree-brother-plugin
```

## Configuration Options

**TODO**

## Notes

### PT-750W

To print to the PT-750W printer, the *Use Compression* option [must be enabled](https://github.com/pklaus/brother_ql/issues/78).
