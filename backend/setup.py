from setuptools import setup, find_packages

setup(
    name="budget-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "firebase-admin",
        "python-jose[cryptography]",
        "python-multipart",
        "pydantic",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "httpx",
            "pytest-asyncio",
        ],
    },
    python_requires=">=3.9",
)

