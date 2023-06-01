"""Brother label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the brother_ql library.
"""

# Required brother_ql libs
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.models import ALL_MODELS
from brother_ql.labels import ALL_LABELS

# translation
from django.utils.translation import ugettext_lazy as _

from inventree_brother.version import BROTHER_PLUGIN_VERSION

# InvenTree plugin libs
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin

# Image library
from PIL import Image

def get_model_choices():
    """
    Returns a list of available printer models
    """

    return [(model.name, model.name) for model in ALL_MODELS]


def get_label_choices():
    """
    Return a list of available label types
    """

    return [(label.identifier, label.name) for label in ALL_LABELS]


def get_rotation_choices():
    """
    Return a list of available rotation angles
    """

    return [(f"{degree}", f"{degree}°") for degree in [0, 90, 180, 270]]


class BrotherLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):

    AUTHOR = "Oliver Walters"
    DESCRIPTION = "Label printing plugin for Brother printers"
    VERSION = BROTHER_PLUGIN_VERSION

    NAME = "Brother Labels"
    SLUG = "brother"
    TITLE = "Brother Label Printer"

    SETTINGS = {
        'MODEL': {
            'name': _('Printer Model'),
            'description': _('Select model of Brother printer'),
            'choices': get_model_choices,
            'default': 'PT-P750W',
        },
        'LABEL': {
            'name': _('Label Media'),
            'description': _('Select label media type'),
            'choices': get_label_choices,
            'default': '12',
        },
        'IP_ADDRESS': {
            'name': _('IP Address'),
            'description': _('IP address of the brother label printer'),
            'default': '',
        },
        'AUTO_CUT': {
            'name': _('Auto Cut'),
            'description': _('Cut each label after printing'),
            'validator': bool,
            'default': True,
        },
        'ROTATION': {
            'name': _('Rotation'),
            'description': _('Rotation of the image on the label'),
            'choices': get_rotation_choices,
            'default': '0',
        },
        'COMPRESSION': {
            'name': _('Compression'),
            'description': _('Enable image compression option (required for some printer models)'),
            'validator': bool,
            'default': False,
        },
        'HQ': {
            'name': _('High Quality'),
            'description': _('Enable high quality option (required for some printers)'),
            'validator': bool,
            'default': True,
        },
    }

    def print_label(self, **kwargs):
        """
        Send the label to the printer
        """

        # TODO: Add padding around the provided image, otherwise the label does not print correctly
        # ^ Why? The wording in the underlying brother_ql library ('dots_printable') seems to suggest
        # at least that area is fully printable.
        # TODO: Improve label auto-scaling based on provided width and height information

        # Extract width (x) and height (y) information
        # width = kwargs['width']
        # height = kwargs['height']
        # ^ currently this width and height are those of the label template (before conversion to PDF
        # and PNG) and are of little use

        # Extract image from the provided kwargs
        label_image = kwargs['png_file']

        # Read settings
        model = self.get_setting('MODEL')
        ip_address = self.get_setting('IP_ADDRESS')
        media_type = self.get_setting('LABEL')

        # As the brother_ql library only accepts an image with exactly the right size for the label type,
        # we need to resize the image. For now just center the image with some whitespace around the side,
        # but ideally this plugin or maybe the label printing base module should provide some formatting
        # options for scaling, margins, etc.
        # TODO: correctly handle case where label image is bigger than printable area
        for media_specifications in ALL_LABELS:
            if media_specifications.identifier == media_type:
                printable_dimensions = media_specifications.dots_printable
        printable_image = Image.new("RGB", printable_dimensions, "white")
        margin_left = (printable_dimensions[0] - label_image.width) // 2
        margin_top = (printable_dimensions[1] - label_image.height) // 2
        printable_image.paste(label_image, (margin_left, margin_top))

        # Check if red labels used
        if media_type in ['62red']:
            red = True
        else:
            red = False

        printer = BrotherQLRaster(model=model)

        # Generate instructions for printing
        params = {
            'qlr': printer,
            'images': [printable_image],
            'label': media_type,
            'cut': self.get_setting('AUTO_CUT'),
            'rotate': self.get_setting('ROTATION'),
            'compress': self.get_setting('COMPRESSION'),
            'hq': self.get_setting('HQ'),
            'red': red,
        }

        instructions = convert(**params)

        send(
            instructions=instructions,
            printer_identifier=f'tcp://{ip_address}',
            backend_identifier='network',
            blocking=True
        )
