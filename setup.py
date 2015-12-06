from setuptools import setup

setup(
  name="anonbox",
  version="0.0.1",

  packages=["anonbox"],
  entry_points={
    "console_scripts": [
      "anonbox = anonbox.__main__:main"
    ]
  },
)
