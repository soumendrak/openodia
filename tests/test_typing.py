from importlib import resources

from mypy import api

SNIPPET = """
from openodia import ud
reveal_type(ud.remove_stopwords("a b"))
reveal_type(ud.remove_stopwords(["a"], get_str=True))
reveal_type(ud.remove_stopwords("a", get_str=False))
"""


def test_package_ships_py_typed_marker():
    assert resources.files("openodia").joinpath("py.typed").is_file()


def test_remove_stopwords_return_type_follows_get_str():
    stdout, _, status = api.run(["--config-file=", "--no-incremental", "-c", SNIPPET])

    assert status == 0
    revealed = [line.split('"')[1].replace("builtins.", "") for line in stdout.splitlines() if "Revealed type" in line]
    assert revealed == ["list[str]", "str", "list[str]"]
