"""
Copyright 2019 Brain Electrophysiology Laboratory Company LLC

Licensed under the ApacheLicense, Version 2.0(the "License");
you may not use this module except in compliance with the License.
You may obtain a copy of the License at:

http: // www.apache.org / licenses / LICENSE - 2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
ANY KIND, either express or implied.
"""
import pytest
import time

from ..cached_property import cached_property, drop_cache

sleep_time = 0.4


@pytest.fixture
def dummy():
    class Dummy:
        @cached_property
        def takes_some_time(self):
            """some documentation code"""
            time.sleep(sleep_time)
            return 'unexpected time span'
    return Dummy()


def test_cached_property(dummy):
    """Test that property is cached"""
    # Test that doc string is transferred by decorator
    assert type(dummy).takes_some_time.__doc__ == """some documentation code"""
    # first time takes 1 second
    t0 = time.time()
    err = dummy.takes_some_time
    dt = time.time()-t0
    assert dt == pytest.approx(sleep_time, 1e-1), err
    # second time takes zero second, because result is cached
    # here we also test that the output didn't change.
    t0 = time.time()
    assert err == dummy.takes_some_time, "Cache has wrong value"
    dt = time.time()-t0
    assert dt == pytest.approx(0.0, abs=1e-1), err


def test_drop_cache(dummy):
    """test that cache is removed"""
    # test that `drop_cache` can fail if no cache exists
    drop_cache(dummy, 'takes_some_time', permissive=True)
    with pytest.raises(ValueError):
        drop_cache(dummy, 'takes_some_time')
    t0 = time.time()
    err = dummy.takes_some_time
    dt = time.time()-t0
    assert dt == pytest.approx(sleep_time, 1e-1), err
    drop_cache(dummy, 'takes_some_time')
    t0 = time.time()
    assert err == dummy.takes_some_time, "Function output changed"
    dt = time.time()-t0
    assert dt == pytest.approx(sleep_time, abs=1e-1), err
