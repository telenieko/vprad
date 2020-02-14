import inspect
import logging
from os.path import relpath

from vprad.helpers import log_with_caller


def test_log_with_caller(mocker):
    stub = mocker.stub(name='logger')
    stub.log = mocker.stub(name='log')
    log_with_caller(stub, logging.WARNING, 1,
                    "Error! %s", 'warning')
    frame_info: inspect.FrameInfo = inspect.stack()[0]
    filename = relpath(frame_info.filename)
    prefix = f"{filename}:{frame_info.lineno-1}:{frame_info.function} Error! %s"
    stub.log.assert_called_once_with(logging.WARNING, prefix, 'warning')
