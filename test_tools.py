import json

import pytest

from toolagent.tools import calculator, position_size, run_tool


def test_calculator_basic():
    assert calculator("(12+8)*3-4") == "56"
    assert calculator("17.5/100*2480") == "434"


def test_calculator_rejects_unsafe_input():
    with pytest.raises(ValueError):
        calculator("__import__('os').system('echo hi')")
    with pytest.raises(ValueError):
        calculator("2**1000")


def test_calculator_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculator("10/0")


def test_position_size():
    out = json.loads(position_size(5000, 1, 25))
    assert out == {"risk_amount": 50.0, "lots": 0.2}


def test_position_size_validates_inputs():
    with pytest.raises(ValueError):
        position_size(5000, 0, 25)


def test_unknown_tool():
    with pytest.raises(KeyError):
        run_tool("nope", {})
