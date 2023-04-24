import time


class Profiler:
    def __init__(self):
        self._st = time.time()

    def reload(self):
        self._st = time.time()

    @property
    def elapsed(self):
        result = time.time() - self._st
        return round(result, 2)
