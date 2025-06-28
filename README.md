![image](docs/cover-pic.png)

<h4 align="center">
  <a href="https://img.shields.io/badge/Python-3.9-blue"><img alt="python 3.9" src="https://img.shields.io/badge/Python-3.9-blue"></a>
  <a href="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml"><img alt="Code coverage" src="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml/badge.svg"></a>
  <a href="https://github.com/soumendrak/openodia/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://codecov.io/gh/soumendrak/openodia"><img alt="code coverage" src="https://codecov.io/gh/soumendrak/openodia/branch/main/graph/badge.svg?token=1TOQIKGDQ2"/></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia?ref=badge_shield" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia.svg?type=shield" alt="license"/></a>
  <a href="https://pepy.tech/project/openodia" alt="downloads"><img src="https://static.pepy.tech/personalized-badge/openodia?period=total&units=none&left_color=black&right_color=orange&left_text=Downloads"/></a>
</h4>


- `openodia` is a Python package which contains various tools on Odia language.
- The short term goal of this package is to not make state-of-the-art methods, but to make tools which work.

## Install

- Please install any version of Python which is higher than or equal to Python 3.9. It should work. 
- The library is tested in python 3.9 version.

```bash
pip install openodia
```

- If you want to directly build from the binary, please clone the repo and run `setup.py`.
```shell
git clone https://github.com/soumendrak/openodia.git
python setup.py install
```

## Usage and Documentation

For usage and further documentation please visit the [Documentation](https://openodia.soumendrak.com/) page.

### Stemming

Basic stemming support is available via a simple rule-based stemmer.

```python
from openodia import stem_word, stem_text

stem_word("ପିଲାମାନେ")
```
will return:

```python
'ପିଲା'
```

`stem_text` can be used for whole sentences:

```python
stem_text("ପିଲାମାନେ ବইଗୁଡ଼ିକ ପଢ଼ୁଛନ୍ତି")
```
which gives `"ପିଲା ବଇ ପଢ଼ୁଛ"`.

## License

<a align="center">
<a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia?ref=badge_large" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia.svg?type=large"/></a>
</a>
