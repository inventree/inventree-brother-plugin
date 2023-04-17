[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![PEP](https://github.com/inventree/inventree-python/actions/workflows/pep.yaml/badge.svg)


# inventree-brother-plugin

A label printing plugin for [InvenTree](https://inventree.org), which provides support for the [Brother label printers](https://www.brother.com.au/en/products/all-labellers/labellers).

This plugin supports printing to *some* Brother label printers with network (wired or WiFi) support. Refer to the [brother_ql docs](https://github.com/pklaus/brother_ql/blob/master/brother_ql/models.py) for a list of label printers which are directly supported.

## Installation

Install this plugin manually as follows:

```
pip install inventree-brother-plugin
```

Or, add to your `plugins.txt` file to install automatically using the `invoke install` command:

```
inventree-brother-plugin
```
 
### Debian / Ubuntu requirements

The following command can be used to install all OS-requirements on Debian / Ubuntu-based distros:
```bash
apt install build-essential libpoppler-cpp-dev pkg-config poppler-utils
```

You might also need the following Python packages:
```bash
pip install pdf-info python-poppler
```

## Configuration Options

**TODO**
