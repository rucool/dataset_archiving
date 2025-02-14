from setuptools import setup, find_packages
from dataset_archiving import __version__

setup(
    name='dataset_archiving',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/rucool/dataset_archiving',
    author='Laura Nazzaro, Lori Garzio',
    author_email='nazzaro@marine.rutgers.edu, lgarzio@marine.rutgers.edu',
    description='Tools to post-process and prepare datasets for archiving.'
)
