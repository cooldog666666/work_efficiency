from setuptools import setup, find_packages
setup(
    name='github_team_members',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'PyGithub',
    ],
    entry_points='''
        [console_scripts]
        github_team_members=github_team_members:main
    ''',
)
