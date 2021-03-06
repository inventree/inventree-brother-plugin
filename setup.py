# -*- coding: utf-8 -*-

import setuptools

from inventree_brother.version import BROTHER_PLUGIN_VERSION

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name="inventree-brother-plugin",

    version=BROTHER_PLUGIN_VERSION,

    author="Oliver Walters",

    author_email="oliver.henry.walters@gmail.com",

    description="Brother label printer plugin for InvenTree",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree label printer printing inventory",

    url="https://github.com/inventree/inventree-brother-plugin",

    license="MIT",

    packages=setuptools.find_packages(),

    install_requires=[
        'brother_ql @ git+https://github.com/pklaus/brother_ql/@56cf4394ad750346c6b664821ccd7489ec140dae',
    ],

    setup_requires=[
        "wheel",
        "twine",
    ],

    python_requires=">=3.6",

    entry_points={
        "inventree_plugins": [
            "BrotherLabeLPlugin = inventree_brother.brother_plugin:BrotherLabelPlugin"
        ]
    },
)
