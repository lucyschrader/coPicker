from setuptools import find_packages, setup

setup(
	name="picker",
	version='1.0.0.a1',
	description="Tool to select Te Papa collection items.",
	license='MIT',
	classifiers=[
		'Private :: Do not upload',
		'Development Status :: 3 - Alpha',
		'Framework :: Flask',
		'Intended Audience :: Science/Research',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: English',
		'Programming Language :: Python',
	],
	packages = find_packages(),
	include_package_data=True,
	install_requires=[
		"flask",
		"requests",
		"sqlite3",
	],
	python_requires='>3.11'
)