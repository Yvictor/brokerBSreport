from setuptools import setup, find_packages

setup(
    name='brokerBSreport',
    version='0.0.1',
    author='Yvictor',
    author_email='fate2314@gmail.com',
    packages=find_packages(),
    install_requires=["requests",
                      "keras",
                      "bs4",
                      "lxml",
                      "pandas",
                      "html5lib",
                      "numpy",
                      "pillow",
                      "raven",
                      "tables",
                      "google-api-python-client",
                      "h5py",],
)