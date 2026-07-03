[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![PEP](https://github.com/inventree/inventree-python/actions/workflows/pep.yaml/badge.svg)


# inventree-brother-plugin

A label printing plugin for [InvenTree](https://inventree.org), which provides support for the [Brother label printers](https://www.brother.com.au/en/products/all-labellers/labellers).

This plugin supports printing to *some* Brother label printers with network (wired or WiFi) support. Refer to the [brother-label](https://github.com/fuzeman/brother-label) repository for more detailed information on supported devices and label media.

## Installation

### Minimum Requirements

> [!IMPORTANT]
> This plugin now requires the "modern" InvenTree UI - version `0.18.0` or newer. The plugin will not function correctly on an InvenTree instance below version `0.18.0`

### Installation Procedure

Install this plugin manually as follows:

```
pip install inventree-brother-plugin
```

Or, add to your `plugins.txt` file to install automatically using the `invoke install` command:

```
inventree-brother-plugin
```

Now open your InvenTree's "Admin Center > Plugins" page to activate the plugin. Next, read below for instructions on setting up a printer via "Admin Center > Machines".

## Setup a machine instance for a Brother Label Printer

This plugin provides a driver for the machine registry in InvenTree, where multiple instances of this driver can
be set up for each physical label printer you want to connect to. Each machine has its own individual configuration set.

To set up a new machine, go to "Admin Center > Machines" and hit the "+" button. Now choose a name for this specific printer, select "Label Printer" as machine type and "Brother Label Printer Driver" as a driver, then submit. The new printer will now be listed in the machines table. To configure the printer, click on its line to open the "Machine detail" panel where you can set the "Driver Settings" to match your label printer.

## Configuration Options
The following list gives an overview of the available settings. Refer to the [brother-label](https://github.com/fuzeman/brother-label) repository for more detailed information on supported devices and label media.

* **Printer Model**
  
  Currently supported models are: 

   - ***QL Series:*** QL-500, QL-550, QL-560, QL-570, QL-580N, QL-600, QL-650TD, QL-700, QL-710W, QL-720NW, QL-800, QL-810W, QL-820NWB
   - ***QL 10 Series:*** QL-1050, QL-1060N
   - ***QL 11 Series:*** QL-1100, QL-1100NWB, QL-1115NWB
   - ***PT Series:*** PT-P750W, PT-P900W, PT-P950NW
   - ***PTE Series:*** PT-E550W

* **IP Address**
  
  If connected via TCP/IP, specify the IP address here.

* **USB Device**
  
  If connected via USB, specify the device identifier here (VENDOR_ID:PRODUCT_ID/SERIAL_NUMBER, e.g. from `lsusb`).

* **Compression** *(Default: Disabled)*
  
  Set image compression (required for some printers).

* **High Quality** *(Default: Enabled)*

  Print in high quality (required for some printers).

* **Dithering** *(Default: Disabled)*
   
  Enables grayscale-dithering for nicer logos and watermarks  

* **Label Media** *(Default: 12)*
  
  Select the size and type of the label media (label media may not be supported on all devices).

   - ***Endless (W):*** 6, 9, 12, 18, 24, 29, 36, 38, 50, 54, 62, 62red, 102, 103, 104
   - ***Rectangle (WxH):*** 17x54, 17x87, 23x23, 29x42, 29x90, 39x48, 39x90, 52x29, 54x29, 60x86, 62x29, 62x100, 102x51, 102x152, 103x164
   - ***Round (dia):*** 12, 24, 58

* **Rotation** *(Default: 0)*
  
  Rotation of the image on the label. Either 0, 90, 180 or 270 degrees.

* **Auto Cut** *(Default: Enabled)*
  
  Cut each label after printing.

* **Auto Cut Every** *(Default: Enabled)*
  
  Cut every n-th label.

* **Auto Cut End** *(Default: Enabled)*
  
  Feed and cut after last label is printed.

* **Half Cut** *(Default: Enabled)*
  
  Half-cut labels.

## Troubleshooting

### Known Issues

**Device appears to start printing, and may feed tape, but halts before completing the label.**

1. Some devices may require ***Compression*** to be enabled for printing, update machine settings and try again.

2. Some devices may require ***High Quality*** to be enabled for printing, update machine settings and try again.