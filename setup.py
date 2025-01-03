from setuptools import setup, find_packages

setup(
    name="stream_comparison",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "m3u8",
        "requests",
        "numpy",
        "scipy",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "compare-streams=stream_comparison.compare:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to compare audio streams (HLS and MP3/Icecast)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stream_comparison",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
