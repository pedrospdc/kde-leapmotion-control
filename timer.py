from time import time


class Timer(object):
    configs = {
        'scroll': 1.5,
        'scroll_sleep': 0.8
    }
    timers = {}

    def start_timer(self, id_):
        self.timers[id_] = time()

    def check_timer(self, id_):
        if id_ in self.timers:
            if time() - self.timers[id_] >= self.configs[id_]:
                return True
        return False

    def clean_timers(self):
        now = time()
        for id_, timer in self.timers.iteritems():
            if now - timer >= self.configs[id_]:
                del timer