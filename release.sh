# $1 is the current version, for e.g. 0.0.5
# $2 is the release severity major.minor.patch
bumpversion --allow-dirty --current-version $1 $2 setup.py openodia/__init__.py
git commit -am "version upgraded"
git push
python setup.py sdist bdist_wheel
twine check dist/*
twine upload --skip-existing dist/*
