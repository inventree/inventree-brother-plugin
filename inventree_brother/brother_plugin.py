"""
Label printing plugin for InvenTree.
Supports direct printing of labels to networked label printers,
using the brother_ql library.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
from plugin import IntegrationPluginBase
from plugin.mixins import LabelPrintingMixin, SettingsMixin


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


class BrotherLabelPlugin(LabelPrintingMixin, SettingsMixin, IntegrationPluginBase):

    AUTHOR = "Oliver Walters"
    DESCRIPTION = "Label printing plugin for Brother printers"
    VERSION = BROTHER_PLUGIN_VERSION

    PLUGIN_NAME = "Brother"
    PLUGIN_SLUG = "brother"
    PLUGIN_TITLE = "Brother Label Printer"

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
    }

    def print_label(self, label_image):
        """
        Send the label to the printer
        """

        # Read settings
        model = self.get_setting('MODEL')
        label = self.get_setting('LABEL')
        ip_address = self.get_setting('IP_ADDRESS')
        auto_cut = self.get_setting('AUTO_CUT')

        printer = BrotherQLRaster(model=model)

        # Generate instructions for printing
        params = {
            'qlr': printer,
            'images': [label_image],
            'cut': auto_cut,
            'rotate': '270',  # Required rotation for correct printing
            'hq': True,
            'label': label,
        }

        if model in ['PT-P750W', 'PT-P900W']:
            # Override compression setting for these printers
            params['compress'] = True

        instructions = convert(**params)

        send(
            instructions=instructions,
            printer_identifier=f'tcp://{ip_address}',
            backend_identifier='network',
            blocking=True
        )
