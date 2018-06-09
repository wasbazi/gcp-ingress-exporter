import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='kubernetes-ingress-exporter',
    version='0.1',
    description='Kubernetes Ingress Exporter to Prometheus',
    packages=[],
    include_package_data=True,
    long_description=read('README.md'),
    install_requires=[
        'google-api-python-client',
        'kubernetes',
        'prometheus_client',
        'oauth2client',
        'requests'
    ]
)
