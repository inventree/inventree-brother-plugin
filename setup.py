# -*- coding: utf-8 -*-

import importlib
import importlib.util
import os
import setuptools

"""Read the plugin version from the source code."""
module_path = os.path.join(
    os.path.dirname(__file__), "inventree_brother", "__init__.py"
)
spec = importlib.util.spec_from_file_location("inventree_brother", module_path)
inventree_brother = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventree_brother)

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()


setuptools.setup(
    name="inventree-brother-plugin",
    version=inventree_brother.BROTHER_PLUGIN_VERSION,
    author="Oliver Walters",
    author_email="oliver.henry.walters@gmail.com",
    description="Brother label printer plugin for InvenTree",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="inventree label printer printing inventory",
    url="https://github.com/inventree/inventree-brother-plugin",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=[
        "brother-ql-inventree>=1.1",
    ],
    setup_requires=[
        "wheel",
        "twine",
    ],
    python_requires=">=3.9",
    entry_points={
        "inventree_plugins": [
            "BrotherLabeLPlugin = inventree_brother.brother_plugin:BrotherLabelPlugin"
        ]
    },
)
