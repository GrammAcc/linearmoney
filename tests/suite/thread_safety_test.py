import threading

import pytest

import linearmoney as lm

redundancy = 100


@pytest.mark.filterwarnings("ignore: Exception in Thread")
def test_race_condition_is_reproducible(FixtExcThread):
    """Ensure that we can reliably force a race condition in a test case.

    If this test fails, the results of all other test cases in this file are
    inconclusive as they all rely on our ability to force a race condition at a
    specific point.
    """

    for _ in range(redundancy):
        _value = 0
        ev = threading.Event()

        def thread1():
            global _value
            _value = 1
            ev.wait()  # Force a race condition.
            _value = 2
            ev.clear()

        def thread2():
            global _value
            assert _value == 1  # Should still be 1 if we were able to force a race.
            ev.set()

        t1 = FixtExcThread(target=thread1)
        t2 = FixtExcThread(target=thread2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()


@pytest.mark.filterwarnings("ignore: Exception in Thread")
@pytest.mark.usefixtures("fixt_restore_global_cache")
def test_mutate_global_cache_in_main_thread(FixtExcThread):
    """The properties of the cache should be copied from the main thread to any
    new threads when they are started."""

    assert lm.cache.get_base_size() != 512
    lm.cache.set_base_size(512)

    def thread1():
        assert lm.cache.get_base_size() == 512

    t1 = FixtExcThread(target=thread1)
    t1.start()
    t1.join()


@pytest.mark.filterwarnings("ignore: Exception in Thread")
@pytest.mark.usefixtures("fixt_restore_global_cache")
def test_mutate_global_cache_in_subthread(FixtExcThread):
    """The properties of the cache should be thread local if set in a thread other than
    the main thread."""

    assert lm.cache.get_base_size() != 512
    lm.cache.set_base_size(512)

    ev = threading.Event()

    for _ in range(redundancy):

        def thread1():
            lm.cache.set_base_size(1024)
            ev.wait()  # Force a race condition.
            assert lm.cache.get_base_size() == 1024
            ev.clear()

        def thread2():
            assert lm.cache.get_base_size() == 512
            ev.set()

        t1 = FixtExcThread(target=thread1)
        t2 = FixtExcThread(target=thread2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert lm.cache.get_base_size() == 512


@pytest.mark.filterwarnings("ignore: Exception in Thread")
@pytest.mark.usefixtures("fixt_restore_global_cache")
def test_disable_global_cache_in_subthread(FixtExcThread):
    """Disabling the cache in a subthread should not affect any other threads
    including the main thread."""

    assert lm.cache.is_enabled()

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    ev = threading.Event()

    for _ in range(redundancy):

        def thread1():
            _add1(100)
            assert lm.cache.size(_add1) == 1
            lm.cache.enable(False)
            ev.wait()  # Force a race condition.
            _add1(101)
            assert lm.cache.size(_add1) == 1
            ev.clear()

        def thread2():
            _add1(100)
            assert lm.cache.size(_add1) == 1
            _add1(101)
            assert lm.cache.size(_add1) == 2
            ev.set()

        t1 = FixtExcThread(target=thread1)
        t2 = FixtExcThread(target=thread2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()


@pytest.mark.filterwarnings("ignore: Exception in Thread")
@pytest.mark.usefixtures("fixt_restore_global_cache")
def test_thread_local_cache(FixtExcThread):
    """Subthreads should have their own thread local caches and should not affect
    the main thread's cache."""

    assert lm.cache.is_enabled()

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(100)
    assert lm.cache.size(_add1) == 1

    def thread1():
        for i in range(10):
            _add1(i)
        assert lm.cache.size(_add1) == 10  # Would be 11 if not thread local.

    t1 = FixtExcThread(target=thread1)
    t1.start()
    t1.join()

    assert lm.cache.size(_add1) == 1
