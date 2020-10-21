import pip
import setuptools

# parse "./requirements.txt" using pip's `parse_requirements`
pip_major_version = list(map(int, pip.__version__.split('.')))[0]
if pip_major_version >= 10:
    from pip._internal.req import parse_requirements
else:
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
if pip_major_version >= 20:
    requirements = [str(ir.requirement) for ir in install_reqs]
else:
    requirements = [str(ir.req) for ir in install_reqs]

setuptools.setup(
    name='mffpy',
    version='0.5.5',
    packages=setuptools.find_packages(),
    scripts=['./bin/mff2json.py', './bin/mff2mfz.py'],
    author='Justus Schwabedal, Wayne Manselle',
    author_email='jschwabedal@belco.tech, wayne.manselle@belco.tech',
    maintainer='Evan Hathaway',
    maintainer_email='evan.hathaway@belco.tech',
    description="Reader and Writer for Philips' MFF file format.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
