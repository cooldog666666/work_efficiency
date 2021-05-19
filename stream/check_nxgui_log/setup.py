from setuptools import setup, find_packages
setup(
    name='check_nxgui_log',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        check_nxgui_log=check_nxgui_log:main
    ''',
)
