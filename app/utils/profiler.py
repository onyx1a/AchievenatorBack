import timeit


class InlineProfiler:
    def __init__(self):
        self._st = timeit.default_timer()

    def reload(self):
        self._st = timeit.default_timer()

    @property
    def elapsed(self):
        result = timeit.default_timer() - self._st
        return round(result, 2)


class GlobalProfiler:
    def __init__(self):
        self.info = {}

    def add_data(self, idx, data):
        self.info.setdefault(idx, []).append(data)

    def reset(self):
        self.info.clear()

    def get_statistic(self):
        print("---")
        for k, v in self.info.items():
            print(k, round(sum(v), 2))
        print("---")
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
