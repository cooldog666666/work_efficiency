from setuptools import setup, find_packages
setup(
    name='github_check_pr_status',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'PyGithub',
        'paramiko',
    ],
    entry_points='''
        [console_scripts]
        github_check_pr_status=github_check_pr_status:main
    ''',
)
