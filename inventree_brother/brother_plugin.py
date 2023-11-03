"""Brother label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the brother_ql library.
"""

# Required brother_ql libs
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.models import ALL_MODELS
from brother_ql.labels import ALL_LABELS, FormFactor

# translation
from django.utils.translation import ugettext_lazy as _

# printing options
from rest_framework import serializers

from inventree_brother.version import BROTHER_PLUGIN_VERSION

# InvenTree plugin libs
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin

# Image library
from PIL import ImageOps


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


class BrotherLabelSerializer(serializers.Serializer):
    """Custom serializer class for BrotherLabelPlugin.

    Used to specify printing parameters at runtime
    """

    copies = serializers.IntegerField(
        default=1,
        label=_('Copies'),
        help_text=_('Number of copies to print'),
    )


class BrotherLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):

    AUTHOR = "Oliver Walters"
    DESCRIPTION = "Label printing plugin for Brother printers"
    VERSION = BROTHER_PLUGIN_VERSION

    NAME = "Brother Labels"
    SLUG = "brother"
    TITLE = "Brother Label Printer"

    PrintingOptionsSerializer = BrotherLabelSerializer

    # Use background printing
    BLOCKING_PRINT = False

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

        # Printing options requires a modern-ish InvenTree backend,
        # which supports the 'printing_options' keyword argument
        options = kwargs.get('printing_options', {})
        n_copies = int(options.get('copies', 1))

        # Look for png data in kwargs (if provided)
        label_image = kwargs.get('png_file', None)

        if not label_image:
            # Convert PDF to PNG
            pdf_data = kwargs['pdf_data']
            label_image = self.render_to_png(label=None, pdf_data=pdf_data)

        # Read settings
        model = self.get_setting('MODEL')
        ip_address = self.get_setting('IP_ADDRESS')
        media_type = self.get_setting('LABEL')

        # Get specifications of media type
        media_specs = None
        for label_specs in ALL_LABELS:
            if label_specs.identifier == media_type:
                media_specs = label_specs

        rotation = int(self.get_setting('ROTATION')) + 90
        rotation = rotation % 360

        if rotation in [90, 180, 270]:
            label_image = label_image.rotate(rotation, expand=True)

        try:
            # Resize image if media type is a die cut label (the brother_ql library only accepts images
            # with a specific size in that case)
            # TODO: Make it generic for all media types
            # TODO: Add GUI settings to configure scaling and margins
            if media_specs.form_factor in [FormFactor.DIE_CUT, FormFactor.ROUND_DIE_CUT]:
                # Scale image to fit the entire printable area and pad with whitespace (while preserving aspect ratio)
                printable_image = ImageOps.pad(label_image, media_specs.dots_printable, color="white")

            else:
                # Just leave image as-is
                printable_image = label_image
        except AttributeError as e:
            raise AttributeError("Could not find specifications of label media type '%s'" % media_type) from e
        except Exception as e:
            raise e

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
            'rotate': 0,
            'compress': self.get_setting('COMPRESSION'),
            'hq': self.get_setting('HQ'),
            'red': red,
        }

        instructions = convert(**params)

        for _i in range(n_copies):
            send(
                instructions=instructions,
                printer_identifier=f'tcp://{ip_address}',
                backend_identifier='network',
                blocking=True
            )
