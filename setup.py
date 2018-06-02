from setuptools import setup

setup(
	name = '_magiccube',
	version = '1.0',
	packages = ['_magiccube'],
	dependency_links = [
		'https://github.com/guldfisk/mtgorp/tarball/master#egg=mtgorp-1.0',
		'https://github.com/guldfisk/orp/tarball/master#egg=orp-1.0',
		'https://github.com/guldfisk/mtgimg/tarball/master#egg=mtgimg-1.0',
	],
	install_requires = [
		'lazy-property',
		'mtgorp',
		'orp',
		'mtgimg',
		'Pillow',
		'promise',
		'numpy',
		'requests',
		'aggdraw',
	],
)