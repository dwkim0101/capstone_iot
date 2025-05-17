# setup.py 파일 생성
from setuptools import setup, find_packages

setup(
    name="duet_monitor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyserial==3.5",
        "pandas==2.2.1",
        "matplotlib==3.8.3",
        "numpy>=1.24.0"
    ],
    entry_points={
        'console_scripts': [
            'duet-monitor=duet_monitor.main:main',
        ],
    },
    python_requires='>=3.8',
)