"""Brother label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the brother_ql library.
"""

from brother_label import BrotherLabel, Media

from django.db import models
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.request import Request

from . import BROTHER_PLUGIN_VERSION

# InvenTree plugin libs
from report.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine

brother = BrotherLabel()

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
            "DITHER": {
                "name": _("Dithering"),
                "description": _(
                    "Enable grayscale-dithering for nicer logos and watermarks"
                ),
                "validator": bool,
                "default": False,
                "required": True,
            },
            "LABEL": {
                "name": _("Label Media"),
                "description": _("Select label media type"),
                "choices": self.get_label_choices,
                "default": "12",
                "required": True,
            },
            "ROTATION": {
                "name": _("Rotation"),
                "description": _("Rotation of the image on the label"),
                "choices": self.get_rotation_choices,
                "default": "0",
                "required": True,
            },
            "AUTO_CUT": {
                "name": _("Auto Cut"),
                "description": _("Cut each label after printing"),
                "validator": bool,
                "default": True,
                "required": True,
            },
            "AUTO_CUT_EVERY": {
                "name": _("Auto Cut Every"),
                "description": _("Cut every n-th label"),
                "validator": int,
                "default": 1,
                "required": True,
            },
            "AUTO_CUT_END": {
                "name": _("Auto Cut End"),
                "description": _("Feed and cut after the last label is printed"),
                "validator": bool,
                "default": True,
                "required": True,
            },
            "HALF_CUT": {
                "name": _("Half Cut"),
                "description": _("Half-cut labels"),
                "validator": bool,
                "default": True,
                "required": True,
            },
        }

        super().__init__(*args, **kwargs)

    def get_model_choices(self, **kwargs):
        """Returns a list of available printer models"""
        return [(model, device.name) for (model, device) in brother.devices.items()]

    def get_label_choices(self, **kwargs):
        """Return a list of available label types"""
        return [(str(media), media.description) for media in list(Media)]

    def get_rotation_choices(self, **kwargs):
        """Return a list of available rotation angles"""
        return [(f"{degree}", f"{degree}°") for degree in [0, 90, 180, 270]]

    def init_machine(self, machine: BaseMachineType):
        """Machine initialize hook."""
        # static dummy setting for now, should probably be actively checked for USB printers
        # and maybe by running a simple ping test or similar for networked printers
        machine.set_status(LabelPrinterMachine.MACHINE_STATUS.CONNECTED)

    def print_labels(
        self,
        machine: LabelPrinterMachine,
        label: LabelTemplate,
        items: QuerySet[models.Model],
        **kwargs,
    ) -> JsonResponse | None:
        """Print one or more labels with the provided template and items."""

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
        options = kwargs.get('printing_options', {})

        media = options.get('label', '12')
        copies = int(options.get('copies', 1))
        autocut = options.get('autocut', True)
        autocut_every = int(options.get('autocut_every', 1))
        autocut_end = options.get('autocut_end', True)
        halfcut = options.get('halfcut', True)

        # Calculate rotation
        rotation = int(options.get('rotation', 0)) + 90
        rotation = rotation % 360

        # Read settings
        model = machine.get_setting("MODEL", "D")
        ip_address = machine.get_setting("IP_ADDRESS", "D")
        usb_device = machine.get_setting("USB_DEVICE", "D")
        compress = machine.get_setting("COMPRESSION", "D")
        hq = machine.get_setting("HQ", "D")
        dither = machine.get_setting("DITHER", "D")

        # Select appropriate identifier and backend
        target = ''
        backend = ''

        if ip_address:
            target = f'tcp://{ip_address}'
            backend = 'network'
        elif usb_device:
            target = f'usb://{usb_device}'
            backend = 'pyusb'
        else:
            raise ValueError("No IP address or USB device defined.")

        # Render labels
        labels = [
            self.render_to_png(label, item, **kwargs)
            for item in items
        ]

        # Print labels
        brother.print(
            media,
            [label for label in labels for x in range(copies)],
            autocut=autocut,
            autocut_every=autocut_every,
            autocut_end=autocut_end,
            halfcut=halfcut,
            device=model,
            compress=compress,
            hq=hq,
            dither=dither,
            rotate=rotation,
            target=target,
            backend=backend,
            blocking=True
        )

    def get_printing_options_serializer(
        self, request: Request, *args, **kwargs
    ) -> 'LabelPrinterBaseDriver.PrintingOptionsSerializer':
        """Return a serializer class instance with dynamic printing options."""
        return self.PrintingOptionsSerializer(self, *args, **kwargs)

    class PrintingOptionsSerializer(LabelPrinterBaseDriver.PrintingOptionsSerializer):
        """Printing options serializer for brother labels."""

        def __init__(self, plugin, machine=None, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Configure fields
            self.fields['rotation'].choices = plugin.get_rotation_choices()

            # Configure with machine settings (if available)
            if machine:
                label = machine.get_setting("LABEL", "D")

                # Filter label choices to device model
                self.fields['label'].choices = self.get_label_choices(
                    machine.get_setting("MODEL", "D"),
                    default=label
                )

                # Apply defaults
                self.fields['label'].default = label
                self.fields['rotation'].default = machine.get_setting("ROTATION", "D")
                self.fields['autocut'].default = machine.get_setting("AUTO_CUT", "D")
                self.fields['autocut_every'].default = machine.get_setting("AUTO_CUT_EVERY", "D")
                self.fields['autocut_end'].default = machine.get_setting("AUTO_CUT_END", "D")
                self.fields['halfcut'].default = machine.get_setting("HALF_CUT", "D")
            else:
                # Fallback to all label choices
                self.fields['label'].choices = plugin.get_label_choices()

        def get_label_choices(self, model, default=None):
            device = brother.devices.get(model)

            if not device:
                return [(str(media), media.description) for media in list(Media)]
            
            choices = []

            for label in device.labels:
                if label.media == default:
                    choices.append((label.media, f"{label.name} ({_('default')})"))
                else:
                    choices.append((label.media, label.name))

            return choices

        label = serializers.ChoiceField(
            label=_("Label Media"),
            help_text=_("Select label media type"),
            choices=[],
            default="12",
        )

        rotation = serializers.ChoiceField(
            label=_("Rotation"),
            help_text=_("Rotation of the image on the label"),
            choices=[],
            default="0",
        )

        autocut = serializers.BooleanField(
            default=True,
            label=_("Auto Cut"),
            help_text=_("Automatically cut the label after printing")
        )

        autocut_every = serializers.IntegerField(
            default=1,
            label=_("Auto Cut Every"),
            help_text=_("Cut every n-th label")
        )

        autocut_end = serializers.BooleanField(
            default=True,
            label=_("Auto Cut End"),
            help_text=_("Feed and cut after the last label is printed")
        )

        halfcut = serializers.BooleanField(
            default=True,
            label=_("Half Cut"),
            help_text=_("Half-cut labels")
        )
