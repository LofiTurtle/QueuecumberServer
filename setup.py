from setuptools import setup

setup(
    name='QueuecumberServer',
    packages=['server'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
