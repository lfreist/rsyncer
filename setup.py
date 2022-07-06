from setuptools import setup

from rsyncer.__version__ import __version__, __description__, __title__, __url__, __author__, __author_email__

VERSION = __version__
DESCRIPTION = __description__
with open("README.md", "r") as ld:
    LONG_DESCRIPTION = ld.read()

setup(
    name=__title__,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    packages=[__title__],
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        ],
)
