from setuptools import setup, find_packages

setup(
    name="PyMAAP",
    version="0.1.0",
    author="Samuel Alter",
    author_email="s.r.alter@icloud.com",
    description="PyMAAP: Python Monitoring and Analysis Package.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sralter/pymaap",
    packages=find_packages(include=["pymaap", "pymaap.*"]),
    install_requires=[
        "psutil==6.1.0",
        "pandas==1.5.3",
        "geopandas==0.10.2",
        "matplotlib==3.6.3",
        "seaborn==0.11.2",
        "pytest>=7.4",
        "pytest-cov>=4.1"
    ],
    extras_require={
        "dev": ["pytest", "pytest-cov", "pytest-html", "sphinx", "twine", "build"]
    }
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
