python setup.py sdist bdist_wheel
twine check dist/*
bumpversion --current-version 0.0.0 patch setup.py openodia/__init__.py
twine upload dist/*
