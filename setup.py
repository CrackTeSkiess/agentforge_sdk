"""Setup configuration for aitabletop package.

This package can be installed via pip:
    pip install aitabletop

Or with extras:
    pip install aitabletop[chess,dev]
"""

from setuptools import find_packages, setup

# Read long description from README.md
def read_readme():
    try:
        with open("README.md", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

# Read LICENSE file
def read_license():
    try:
        with open("LICENSE", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "MIT"

setup(
    name="aitabletop",
    version="0.1.0",
    description="AITabletop Python SDK - Build and deploy AI agents for tabletop games",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    license="MIT",
    author="AITabletop Team",
    author_email="support@aitabletop.com",
    url="https://github.com/aitabletop/aitabletop-sdk",
    project_urls={
        "Homepage": "https://aitabletop.com",
        "Documentation": "https://docs.aitabletop.com",
        "Repository": "https://github.com/aitabletop/aitabletop-sdk",
        "Issues": "https://github.com/aitabletop/aitabletop-sdk/issues",
        "Changelog": "https://github.com/aitabletop/aitabletop-sdk/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where=".", exclude=["tests*", "*test*", "main.py"]),
    package_dir={"aitabletop": "aitabletop"},
    package_data={"aitabletop": ["py.typed"]},
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.27.0,<1.0.0",
        "websockets>=13.0,<15.0",
    ],
    extras_require={
        "chess": ["chess>=1.10.0,<2.0.0"],
        "dev": [
            "pytest>=7.0,<9.0",
            "pytest-asyncio>=0.21.0,<1.0.0",
            "ruff>=0.6.0,<1.0.0",
            "mypy>=1.0,<2.0",
            "chess>=1.10.0,<2.0.0",
        ],
        "security": [
            "bandit>=1.7.0",
            "safety>=3.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Typing :: Typed",
    ],
    keywords="reinforcement-learning rl games competition agents ai chess multiplayer bot tabletop board-games",
    entry_points={},
    include_package_data=True,
    zip_safe=False,
)
