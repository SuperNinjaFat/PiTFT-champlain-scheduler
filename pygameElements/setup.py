from setuptools import setup, find_packages

setup(
    name="PiTFT-Scheduler",
    version="0.1",
    packages=find_packages(),

    install_requires=['pandas',
                      'matplotlib',
                      'platform',
                      'datetime',
                      'socket',
                      'pygame',
                      'pylab',
                      'climata',
                      'requests',
                      'bs4',
                      'html',
                      'PIL',
                      # 'sys',
                      # 'fake_rpi',
                      ]
)
