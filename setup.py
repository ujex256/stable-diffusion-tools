from setuptools import setup

setup(
    name="sd-mini-tool",
    version="1.0",
    install_requires=["Pillow", "questionary", "requests", "tqdm"],
    packages=["src"],
    entry_points={
        "console_scripts": [
            "sdt=src.__main__:main"
        ]
    },
    classifiers=[
        "Environment :: Console"
    ],
)
