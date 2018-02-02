import os
import sys
import subprocess

import pytest
from unittest import mock
from unittest.mock import sentinel

from trio import _core
subproc = _core.run_subprocess

from trio._core import _fd_stream

@pytest.fixture
def path(tmpdir):
    return tmpdir.join('test').__fspath__()


@pytest.fixture
def wrapped():
    return mock.Mock(spec_set=io.StringIO)


async def test_basics():
    fd = os.open(os.devnull, os.O_RDONLY)
    os.close(fd)
    async with subproc(sys.executable, "-c", "import sys; sys.exit(0)",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE) as p:
        assert isinstance(p.stdin, _fd_stream.WriteFDStream)
        assert isinstance(p.stdout, _fd_stream.ReadFDStream)
        assert isinstance(p.stderr, _fd_stream.ReadFDStream)
    assert p.returncode == 0
    fd2 = os.open(os.devnull, os.O_RDONLY)
    os.close(fd2)
    assert fd == fd2 # no file descriptor leaks please

async def test_exitcode():
    # call() function with sequence argument
    async with subproc(sys.executable, "-c",
                            "import sys; sys.exit(47)") as p:
        pass
    assert p.returncode == 47

async def test_talking():
    async with subproc(sys.executable, "-c", r"import sys; assert sys.stdin.read(4) == 'foo\n'; sys.stdout.write('bar\n'); sys.stderr.write('baz\n'); sys.exit(0)",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        await p.stdin.send_all(b"foo\n")
        assert await p.stdout.receive_some(42) == b"bar\n"
        assert await p.stderr.receive_some(42) == b"baz\n"
    assert p.returncode == 0

