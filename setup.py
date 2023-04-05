import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# Version number to __version__ variable
exec(open("roimarker/version.py").read())

install_requires = [
        'numpy',
        'tifffile',
        'matplotlib',
        ]

setuptools.setup(
    name="roimarker",
    version=__version__,
    author="Joni Kemppainen",
    author_email="joni.kemppainen@windowslive.com",
    description="A rectangle-ROI annotator using matplotlib",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jkemppainen/roimarker",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3) ",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.0',
)
