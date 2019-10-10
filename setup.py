from setuptools import setup
import os


def package_files(directory):
    paths = []
    for path, directories, file_names in os.walk(directory):
        for filename in file_names:
            paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('magiccube')


setup(
    name = 'magiccube',
    version = '1.0',
    packages = ['magiccube'],
    package_data = {'': extra_files},
    dependency_links = [
        'https://github.com/guldfisk/yeetlong/tarball/master#egg=yeetlong-1.0',
        'https://github.com/guldfisk/mtgorp/tarball/master#egg=mtgorp-1.0',
        'https://github.com/guldfisk/orp/tarball/master#egg=orp-1.0',
        'https://github.com/guldfisk/mtgimg/tarball/master#egg=mtgimg-1.0',
    ],
    install_requires = [
        'lazy-property',
        'yeetlong',
        'mtgorp',
        'orp',
        'mtgimg',
        'Pillow',
        'promise',
        'numpy',
        'requests',
        'aggdraw',
        'appdirs',
        'deap',
        'matplotlib',
        'frozendict',
    ],
)