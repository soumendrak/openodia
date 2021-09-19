"""Setup script for open_odia
Referred: https://github.com/realpython/reader/blob/master/setup.py
"""

import os.path
from setuptools import setup

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

# This call to setup() does all the work
setup(
    name="open_odia",
    version="0.0.0",
    description="Open source Odia language tools",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/soumendrak/open_odia",
    author="Soumendra Kumar Sahoo",
    author_email="proud_odia@outlook.com",
    license="MIT",
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    py_modules=["open_odia"],
    include_package_data=True,
    install_requires=[],
    entry_points={"console_scripts": ["realpython=open_odia.__main__:main"]},
)
