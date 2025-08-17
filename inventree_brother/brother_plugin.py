"""Brother label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the brother_ql library.
"""

# Required brother_ql libs
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.models import ALL_MODELS
from brother_ql.labels import ALL_LABELS, FormFactor

from django.db import models
from django.utils.translation import gettext_lazy as _

from inventree_brother.version import BROTHER_PLUGIN_VERSION

# InvenTree plugin libs
from report.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine

# Image library
from PIL import ImageOps

# Backwards compatibility imports
try:
    from plugin.mixins import MachineDriverMixin
except ImportError:

    class MachineDriverMixin:
        """Dummy mixin for backwards compatibility."""

        pass


class BrotherLabelPlugin(MachineDriverMixin, InvenTreePlugin):
    """Brother label printer driver plugin for InvenTree."""

    AUTHOR = "Oliver Walters"
    DESCRIPTION = "Label printing plugin for Brother printers"
    VERSION = BROTHER_PLUGIN_VERSION

    # Machine registry was added in InvenTree 0.14.0, use inventree-brother-plugin 0.9.0 for older versions
    # Machine driver interface was fixed with 0.16.0 to work inside of inventree workers
    MIN_VERSION = "0.16.0"

    NAME = "Brother Labels"
    SLUG = "brother"
    TITLE = "Brother Label Printer"

    # Use background printing
    BLOCKING_PRINT = False

    def get_machine_drivers(self) -> list:
        """Register machine drivers."""
        return [BrotherLabelPrinterDriver]


class BrotherLabelPrinterDriver(LabelPrinterBaseDriver):
    """Brother label printing driver for InvenTree."""

    SLUG = "brother"
    NAME = "Brother Label Printer Driver"
    DESCRIPTION = "Brother label printing driver for InvenTree"

    def __init__(self, *args, **kwargs):
        """Initialize the BrotherLabelPrinterDriver."""
        self.MACHINE_SETTINGS = {
            "MODEL": {
                "name": _("Printer Model"),
                "description": _("Select model of Brother printer"),
                "choices": self.get_model_choices,
                "default": "PT-P750W",
                "required": True,
            },
            "LABEL": {
                "name": _("Label Media"),
                "description": _("Select label media type"),
                "choices": self.get_label_choices,
                "default": "12",
                "required": True,
            },
            "IP_ADDRESS": {
                "name": _("IP Address"),
                "description": _("IP address of the brother label printer"),
                "default": "",
            },
            "USB_DEVICE": {
                "name": _("USB Device"),
                "description": _(
                    "USB device identifier of the label printer (VID:PID/SERIAL)"
                ),
                "default": "",
            },
            "AUTO_CUT": {
                "name": _("Auto Cut"),
                "description": _("Cut each label after printing"),
                "validator": bool,
                "default": True,
                "required": True,
            },
            "ROTATION": {
                "name": _("Rotation"),
                "description": _("Rotation of the image on the label"),
                "choices": self.get_rotation_choices,
                "default": "0",
                "required": True,
            },
            "COMPRESSION": {
                "name": _("Compression"),
                "description": _(
                    "Enable image compression option (required for some printer models)"
                ),
                "validator": bool,
                "default": False,
                "required": True,
            },
            "HQ": {
                "name": _("High Quality"),
                "description": _(
                    "Enable high quality option (required for some printers)"
                ),
                "validator": bool,
                "default": True,
                "required": True,
            },
        }

        super().__init__(*args, **kwargs)

    def get_model_choices(self, **kwargs):
        """Returns a list of available printer models"""
        return [(model.name, model.name) for model in ALL_MODELS]

    def get_label_choices(self, **kwargs):
        """Return a list of available label types"""
        return [(label.identifier, label.name) for label in ALL_LABELS]

    def get_rotation_choices(self, **kwargs):
        """Return a list of available rotation angles"""
        return [(f"{degree}", f"{degree}°") for degree in [0, 90, 180, 270]]

    def init_machine(self, machine: BaseMachineType):
        """Machine initialize hook."""
        # static dummy setting for now, should probably be actively checked for USB printers
        # and maybe by running a simple ping test or similar for networked printers
        machine.set_status(LabelPrinterMachine.MACHINE_STATUS.CONNECTED)

    def print_label(
        self,
        machine: LabelPrinterMachine,
        label: LabelTemplate,
        item: models.Model,
        **kwargs,
    ) -> None:
        """Send the label to the printer"""

        # TODO: Add padding around the provided image, otherwise the label does not print correctly
        # ^ Why? The wording in the underlying brother_ql library ('dots_printable') seems to suggest
        # at least that area is fully printable.
        # TODO: Improve label auto-scaling based on provided width and height information

        # Extract width (x) and height (y) information
        # width = kwargs['width']
        # height = kwargs['height']
        # ^ currently this width and height are those of the label template (before conversion to PDF
        # and PNG) and are of little use

        # Printing options requires a modern-ish InvenTree backend,
        # which supports the 'printing_options' keyword argument
        options = kwargs.get("printing_options", {})
        n_copies = int(options.get("copies", 1))

        label_image = self.render_to_png(label, item)

        # Read settings
        model = machine.get_setting("MODEL", "D")
        ip_address = machine.get_setting("IP_ADDRESS", "D")
        usb_device = machine.get_setting("USB_DEVICE", "D")
        media_type = machine.get_setting("LABEL", "D")

        # Get specifications of media type
        media_specs = None
        for label_specs in ALL_LABELS:
            if label_specs.identifier == media_type:
                media_specs = label_specs

        rotation = int(machine.get_setting("ROTATION", "D")) + 90
        rotation = rotation % 360

        if rotation in [90, 180, 270]:
            label_image = label_image.rotate(rotation, expand=True)

        try:
            # Resize image if media type is a die cut label (the brother_ql library only accepts images
            # with a specific size in that case)
            # TODO: Make it generic for all media types
            # TODO: Add GUI settings to configure scaling and margins
            if media_specs.form_factor in [
                FormFactor.DIE_CUT,
                FormFactor.ROUND_DIE_CUT,
            ]:
                # Scale image to fit the entire printable area and pad with whitespace (while preserving aspect ratio)
                printable_image = ImageOps.pad(
                    label_image, media_specs.dots_printable, color="white"
                )

            else:
                # Just leave image as-is
                printable_image = label_image
        except AttributeError as e:
            raise AttributeError(
                "Could not find specifications of label media type '%s'" % media_type
            ) from e
        except Exception as e:
            raise e

        # Check if red labels used
        if media_type in ["62red"]:
            red = True
        else:
            red = False

        printer = BrotherQLRaster(model=model)

        # Generate instructions for printing
        params = {
            "qlr": printer,
            "images": [printable_image],
            "label": media_type,
            "cut": machine.get_setting("AUTO_CUT", "D"),
            "rotate": 0,
            "compress": machine.get_setting("COMPRESSION", "D"),
            "hq": machine.get_setting("HQ", "D"),
            "red": red,
        }

        instructions = convert(**params)

        # Select appropriate identifier and backend
        printer_id = ""
        backend_id = ""

        # check IP address first, then USB
        if ip_address:
            printer_id = f"tcp://{ip_address}"
            backend_id = "network"
        elif usb_device:
            printer_id = f"usb://{usb_device}"
            backend_id = "pyusb"
        else:
            # Raise error when no backend is defined
            raise ValueError("No IP address or USB device defined.")

        for _i in range(n_copies):
            send(
                instructions=instructions,
                printer_identifier=printer_id,
                backend_identifier=backend_id,
                blocking=True,
            )
