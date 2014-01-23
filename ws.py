from copy import copy
import math
from subprocess import Popen, PIPE

import Leap, sys,subprocess, time
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

workspace_cols = 2
workspace_total = 4


class SampleListener(Leap.Listener):
    def on_connect(self, controller):
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def get_current_workspace(self):
        p1 = Popen(['wmctrl', '-d'], stdout=PIPE)
        p2 = Popen(['awk', "/\*/ {print $1}"], stdin=p1.stdout, stdout=PIPE)
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
        return workspaces[position[1]][position[0]]

    def move_to_workspace(self, workspace_id):
        subprocess.call(['wmctrl', '-s', str(workspace_id)])
        time.sleep(1)

    def lock_screen(self):
        subprocess.Popen(['qdbus', 'org.freedesktop.ScreenSaver', '/ScreenSaver', 'Lock'])
        time.sleep(1)

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        if not frame.hands.is_empty:
            # Get the first hand
            hand = frame.hands[0]

            # Check if the hand has any fingers
            fingers = hand.fingers

            # Gestures
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_SWIPE and len(fingers) in (4, 5):
                    swipe = SwipeGesture(gesture)
                    workspaces = self.generate_workspace_matrix(workspace_total, workspace_cols)
                    current_position = self.get_position(workspaces, self.get_current_workspace())
                    new_position = self.find_new_position(workspaces, current_position, swipe.direction)
                    new_workspace = self.get_workspace_by_position(workspaces, new_position)
                    self.move_to_workspace(new_workspace)
                if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                    self.lock_screen()

        if not (frame.hands.is_empty and frame.gestures().is_empty):
            pass

    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"


def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # Remove the sample listener when done
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
