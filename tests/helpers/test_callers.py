from unittest.mock import ANY

import pytest

from vprad.helpers import call_with_context


def dumb_method(a_param,
                typed_param: int,
                default_param=123,
                default_typed_param: str = '1234'):
    return f"{a_param}/{typed_param}/{default_param}/{default_typed_param}"


def kwargs_method(a_param,
                  **kwargs):
    return f"{a_param}/{len(kwargs.keys())}"


def test_call_with_context(mocker):
    ret = call_with_context(dumb_method, a_param=1, typed_param=2)
    assert ret == "1/2/123/1234"
    m = mocker.patch('vprad.helpers.log_warning')
    # A type that does not match the signature annotation is logged:
    ret = call_with_context(dumb_method, a_param=1, typed_param='2')
    m.assert_called_once_with(ANY, ANY, ANY, 'typed_param', int, str)
    m.reset_mock()
    # Also when the annotation has a default value:
    ret = call_with_context(dumb_method, a_param=1, typed_param=1,
                            default_typed_param=123)
    m.assert_called_once_with(ANY, ANY, ANY, 'default_typed_param', str, int)
    m.reset_mock()


def test_call_with_context_missing():
    with pytest.raises(TypeError, match=r'Missing \'a_param\' parameter to call .*dumb_method\''):
        call_with_context(dumb_method, typed_param=2)


def test_call_with_context_kwargs(mocker):
    ret = call_with_context(kwargs_method, a_param=1, extra=123)
    assert ret == "1/1"
    with pytest.raises(TypeError, match=r'Missing \'a_param\' parameter to call .*kwargs_method\''):
        call_with_context(kwargs_method, extra=123)
