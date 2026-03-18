"""Setup configuration for agentforge package."""

from setuptools import find_packages, setup

setup(
    name="rlarena-agentforge",
    version="0.1.0",
    description="AgentForge Python SDK - Build and deploy RL agents for competitive multiplayer games",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="AgentForge Team",
    author_email="support@agentforge.io",
    url="https://agentforge.io",
    packages=find_packages(where="."),
    package_dir={"agentforge": "agentforge"},
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Typing :: Typed",
    ],
    keywords="reinforcement-learning rl games competition agents ai",
)