from setuptools import setup, find_packages

setup(
    name="uq-digital-twin",
    version="1.0.0",
    description="Uncertainty-Quantified Digital Twin Framework for Safety-Critical Infrastructure Prognostics",
    author="Antigravity Research Consortium",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
