python setup.py sdist bdist_wheel
twine check dist/*
bumpversion --current-version $1 $2 setup.py openodia/__init__.py
twine upload dist/*
