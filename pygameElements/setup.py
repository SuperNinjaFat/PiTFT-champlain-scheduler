from setuptools import setup, find_packages
setup(
    name="PiTFT-Scheduler",
    version="0.1",
    packages=find_packages(),

    install_requires=['pygame',
                      'pandas',
                      'matplotlib',
                      'datetime',
                      'climata',
                      'requests',
                      'bs4',
                      'html',
                      'PIL',
                      # 'platform',
                      # 'socket',
                      # 'sys',
                      # 'fake_rpi',
                      ]
)

