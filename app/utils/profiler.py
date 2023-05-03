import time


class InlineProfiler:
    def __init__(self):
        self._st = time.time()

    def reload(self):
        self._st = time.time()

    @property
    def elapsed(self):
        result = time.time() - self._st
        return round(result, 2)


class GlobalProfiler:
    def __init__(self):
        self.info = {}

    def add_data(self, idx, data):
        self.info.setdefault(idx, []).append(data)

    def reset(self):
        self.info.clear()

    def async_profiler(self, func):
        async def inner(*args, **kwargs):
            prof = InlineProfiler()
            idx = func.__name__
            result = await func(*args, **kwargs)
            self.add_data(idx, prof.elapsed)
            return result

        return inner

    def profiler(self, func):
        def inner(*args, **kwargs):
            prof = InlineProfiler()
            idx = func.__name__
            result = func(*args, **kwargs)
            self.add_data(idx, prof.elapsed)
            return result

        return inner
