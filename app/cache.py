# in-memory cache (and thread safe!)

# simple in memory cache for storing the api responses to avoid repeated calls

import threading

class SimpleCache:
    def __init__(self):
        self._data = {} # the cache data
        self._lock = threading.Lock() # flask way to only let one thread access this portion of code at a time

    def get_or_set(self, key, compute): # lambda gets passed in to compute from client
        #return the cached value for key, computing and storing it on a miss
        with self._lock:
            if key in self._data:
                return self._data[key]
            # compute only called if key is missing (more efficient - one upstream call instead of two)
            value = compute() 
            self._data[key] = value
            return value
