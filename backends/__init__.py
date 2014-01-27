from abc import ABCMeta, abstractmethod
from copy import copy
import subprocess
import math
from time import sleep

from Xlib import X, display, ext, XK, display


class Backend(object):
    __metaclass__ = ABCMeta

    mouse_sensivity = 0.3
    scroll_sensivity = 25
    display_ = display.Display()
    screen = display_.screen()
    active_keys = {'scroll_down': False,
                   'scroll_up': False}

    def get_current_workspace(self):
        p1 = subprocess.Popen(['wmctrl', '-d'], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['awk', "/\*/ {print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        return int(''.join([i for i in p2.communicate()[0] if i.isdigit()]))

    def _find_in_haystack(self, haystack, needle):
        for k, v in enumerate(haystack):
            if needle == v:
                return k
            try:
                if needle in v:
                    return k
            except TypeError:
                continue

    def get_position(self, haystack, needle):
        y = self._find_in_haystack(haystack, needle)
        return [self._find_in_haystack(haystack[y], needle), y]

    def generate_workspace_matrix(self, num_total, num_cols):
        def chunks(l, n):
            """
            Yield successive n-sized chunks from l.
            """
            for i in xrange(0, len(l), n):
                yield l[i:i+n]
        chunk_size = math.ceil(num_total / float(num_cols))
        return list(chunks(range(num_total), int(chunk_size)))

    def find_new_position(self, workspaces, current_position, direction):
        """
        Calculates new workspace position
        """
        move = 0, 0
        if direction[0] > self.mouse_sensivity:
            # move right
            move = 1, 0
        elif direction[0] < -self.mouse_sensivity:
            # move left
            move = -1, 0
        elif direction[1] > self.mouse_sensivity:
            # move up
            move = 0, -1
        elif direction[1] < -self.mouse_sensivity:
            # move down
            move = 0, 1

        new_position = copy(current_position)
        for k, v in enumerate(move):
            new_position[k] += v

        try:
            self.get_workspace_by_position(workspaces, new_position)
        except IndexError:
            del new_position
            return current_position
        else:
            del current_position
            return new_position

    def get_workspace_by_position(self, workspaces, position):
        """
        Returns workspace id by given position
        """
        return workspaces[position[1]][position[0]]

    def move_to_workspace(self, workspace_id):
        """
        Calls WM  move to
        """
        subprocess.call(['wmctrl', '-s', str(workspace_id)])

    @abstractmethod
    def lock_screen(self):
        pass

    def get_screen_size(self):
        return [self.screen.width_in_pixels, self.screen.height_in_pixels]

    def process_pointer(self, pos):
        x = (pos[0] * (self.screen.width_in_pixels / 250)) + (self.screen.width_in_pixels / 2)
        x = min(x, self.screen.width_in_pixels)
        x = max(x, 0)
        y = self.screen.height_in_pixels - (pos[1] * (self.screen.height_in_pixels / 250)) \
            + (self.screen.height_in_pixels / 2)
        y = min(y, self.screen.height_in_pixels)
        y = max(y, 0)
        self.screen.root.warp_pointer(x, y)
        self.display_.flush()

    def click(self):
        ext.xtest.fake_input(self.display_, X.ButtonPress, 1)
        ext.xtest.fake_input(self.display_, X.ButtonRelease, 1)
        self.display_.flush()

    def scroll(self, pitch):
        if pitch >= self.scroll_sensivity:
            ext.xtest.fake_input(self.display_, X.ButtonPress, 4)
            self.active_keys['scroll_up'] = True
        elif pitch <= -self.scroll_sensivity:
            ext.xtest.fake_input(self.display_, X.ButtonPress, 5)
            self.active_keys['scroll_down'] = True
        elif pitch <= self.scroll_sensivity and self.active_keys['scroll_up']:
            ext.xtest.fake_input(self.display_, X.ButtonRelease, 4)
            self.active_keys['scroll_up'] = False
        elif pitch >= -self.scroll_sensivity and self.active_keys['scroll_down']:
            ext.xtest.fake_input(self.display_, X.ButtonRelease, 5)
            self.active_keys['scroll_down'] = False

        self.display_.flush()
        sleep(0.2)
