from setuptools import setup, find_packages

setup(
    name="pyRemoteDict",
    version="0.1.0",
    description="RemoteDict is a lightweight, in-memory key-value store server implemented in Python.",
    author="TechnoJo",
    url="https://github.com/technojo2000/RemoteDict",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
