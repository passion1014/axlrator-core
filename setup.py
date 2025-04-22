# setup.py
from setuptools import setup, find_packages

setup(
    name="axlrator-core",
    version="0.1.0",
    packages=find_packages(),
)

# setup.py 맨 아래에 추가해도 됨 (개발 중 임시)
import setuptools
print("FOUND PACKAGES:", setuptools.find_packages())