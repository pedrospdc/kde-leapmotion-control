import subprocess
from backends import Backend


class KdeBackend(Backend):
    def lock_screen(self):
        subprocess.Popen(['qdbus', 'org.freedesktop.ScreenSaver', '/ScreenSaver', 'Lock'])