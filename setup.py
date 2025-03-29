from setuptools import setup, find_packages

setup(
    name="monitoring_decorators",
    version="0.1.0",
    author="Samuel Alter",
    author_email="s.r.alter@icloud.com",
    description="Python module for execution monitoring, error logging, and performance analysis.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sralter/monitoring_and_analysis",
    packages=find_packages(),
    install_requires=[
        "psutil==6.1.0",
        "pandas==1.5.3",
        "geopandas==0.10.2",
        "matplotlib==3.6.3",
        "seaborn==0.11.2"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
