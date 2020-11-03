from os.path import join
import pip
import setuptools


def v1_ge_v2(module, version):
    """return `module.__version__ >= version`"""

    def v2li(v):
        """`v2li('20.0') == [20, 0]`"""
        return list(map(int, v.split('.')))

    version = v2li(version)
    module = v2li(module)
    # add semver zeros if, e.g., version='20.5.1' and module='20.5'
    if len(version) > len(module):
        module += [0] * (len(version) - len(module))

    # Compare version numbers
    for m, v in zip(module, version):
        if m > v:
            # current SEMVER number larger
            return True
        elif m == v:
            # go to next number
            continue
        # skip `else` case
        break
    else:
        # Version numbers exactly equal
        return True
    # Indeed, `module.__version__ < version`
    return False


# parse "./requirements.txt" using pip's `parse_requirements`
if v1_ge_v2(pip.__version__, '10'):
    from pip._internal.req import parse_requirements
else:
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
if v1_ge_v2(pip.__version__, '20.1'):
    requirements = [str(ir.requirement) for ir in install_reqs]
else:
    requirements = [str(ir.req) for ir in install_reqs]

# We expect "mffpy/version.py" to be very simple:
#
# > __version__ = "x.y.z"
#
# (from one of the answers in
# https://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package)
__version__ = ''
exec(open(join('mffpy', 'version.py')).read())

setuptools.setup(
    name='mffpy',
    version=__version__,
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
