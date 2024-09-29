from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Remote-CLI',
    version='1.0.0',
    ext_modules=cythonize([
        "djangoProject/*.py",
        "djangoProject/anylog_conn/*.py",
        "djangoProject/migrations/*.py"
    ]),
    packages=['djangoProject', 'djangoProject.anylog_conn'],  # Define the main package and sub-packages
    package_data={
        'djangoProject': [
            'migrations/*',
            'static/css/*',
            'templates/*/*.html'  # Adjust to include HTML files in all subdirectories of 'templates'
        ],
        'djangoProject.anylog_conn': ['*']  # Include all files in anylog_conn
    },
    install_requires=[
        'django',
        'requests',
        'pyqrcode[pi]',
        'pypng'
    ],
)
