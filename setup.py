from setuptools import setup

setup(
	name="wsgi_skickarn",
	install_requires=[
		"werkzeug",
	],
	test_suite='nose.collector',
	tests_require=['nose'],
)
