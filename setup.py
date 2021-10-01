"""Setup script for openodia
Referred:   https://github.com/realpython/reader/blob/master/setup.py
            https://realpython.com/pypi-publish-python-package/
"""

import os.path
from setuptools import find_packages, setup

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

# The text of the requirements file
with open(os.path.join(HERE, "requirements.txt")) as rt:
    REQUIREMENTS = rt.readlines()

# This call to setup() does all the work
setup(
    name="openodia",
    version="0.1.1",
    description="Open source Odia language tools",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/soumendrak/openodia",
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
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={"console_scripts": ["openodia=openodia.__main__:main"]},
)
