import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, rate=10, burst=20):
        self.rate = rate
        self.burst = burst
        self.tokens = defaultdict(lambda: burst)
        self.last = defaultdict(time.time)
    
    def consume(self, key: str, tokens=1) -> bool:
        now = time.time()
        elapsed = now - self.last[key]
        self.tokens[key] = min(self.burst, self.tokens[key] + elapsed * self.rate)
        self.last[key] = now
        if self.tokens[key] >= tokens:
            self.tokens[key] -= tokens
            return True
        return False