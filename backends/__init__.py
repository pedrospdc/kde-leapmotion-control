from abc import ABCMeta, abstractmethod
from copy import copy
import subprocess
import math


class Backend(object):
    __metaclass__ = ABCMeta

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
        if direction[0] > 0.5:
            # move right
            move = 1, 0
        elif direction[0] < -0.5:
            # move left
            move = -1, 0
        elif direction[1] > 0.5:
            # move up
            move = 0, -1
        elif direction[1] < -0.5:
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