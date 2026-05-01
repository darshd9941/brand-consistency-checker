from setuptools import setup, find_packages

setup(
    name="brand-consistency-checker",
    version="0.1.0",
    description="eslint for brand design — validates AI-generated outputs against brand rules",
    author="darshd9941",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "rich>=13.0",
        "fastapi>=0.104",
        "uvicorn>=0.24",
        "PyYAML>=6.0",
        "Pillow>=10.0",
        "pydantic>=2.5",
        "python-multipart>=0.0.6",
    ],
    entry_points={
        "console_scripts": [
            "brand-check=brand_checker.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
