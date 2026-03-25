from setuptools import setup

setup(name='otscrape',
      version='0.0.3',
      description='Python API for scraping oddstrader data',
      url='https://github.com/nkgilley/otscrape',
      author='Nolan Gilley',
      license='GPLv2',
      install_requires=['requests>=2.0'],
      packages=['otscrape'],
      zip_safe=True)
