import os
from setuptools import setup
from sitecats import VERSION


PATH_BASE = os.path.dirname(__file__)


f = open(os.path.join(PATH_BASE, 'README.rst'))
README = f.read()
f.close()

setup(
    name='django-sitecats',
    version='.'.join(map(str, VERSION)),
    url='https://github.com/idlesign/django-sitecats',

    description='Django reusable application for content categorization.',
    long_description=README,
    license='BSD 3-Clause License',

    author='Igor `idle sign` Starikov',
    author_email='idlesign@yandex.ru',

    packages=['sitecats'],
    install_requires=['django-etc'],
    include_package_data=True,
    zip_safe=False,

    classifiers=[
        # As in https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: BSD License'
    ],
)

