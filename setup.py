from setuptools import find_packages, setup

setup(name="transifex_api",
      version="0.0.1",
      install_requires=["requests"],
      packages=find_packages('src'),
      package_dir={'': 'src'})
