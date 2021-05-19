from setuptools import setup, find_packages
setup(
    name='check_sanity_log',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        check_sanity_log=check_sanity_log:main
    ''',
)
