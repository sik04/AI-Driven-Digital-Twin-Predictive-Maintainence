from setuptools import setup, find_packages

setup(
    name="intellitwin",
    version="2.0.0",
    description="IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets",
    author="Mayank Singh, Shiksha Pandey, Ruchi Gupta",
    author_email="shikshapandey2004@gmail.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "xgboost>=1.7.0",
        "flask>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
