import sys
import time

import Leap
from Leap import RAD_TO_DEG
from backends.kde import KdeBackend
from timer import Timer

WORKSPACE_COLS = 2
WORKSPACE_TOTAL = 4
GESTURE_SLEEP = 1


class LeapListener(Leap.Listener):
    gestures_lock_time = 0
    backend = None
    fps = 10
    frames = list()
    prev_frames = list()
    active_modes = {'scroll': False}

    def on_init(self, controller):
        self.backend = self.get_backend()()
        self.timer = Timer()

        for f in range(self.fps):
            self.frames.append(controller.frame(f))
            self.prev_frames.append(controller.frame(f + self.fps))

    def on_connect(self, controller):
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP)

    def lock_gestures(self):
        self.gestures_lock_time = time.time()

    def check_gestures_timeout(self):
        if self.gestures_lock_time:
            now = time.time()
            if now - self.gestures_lock_time >= 1:
                self.gestures_lock_time = 0
                return True
            return False
        return True

    def get_backend(self):
        """
        This should return each WM proper backend.
        Currently we just support kde, so the logic will be coded later.
        """
        return KdeBackend

    def flush_buffer(self):
        self.prev_frames[0:self.fps] = self.frames[0:self.fps]

    def get_average_palm_position(self):
        avg = [0, 0, 0]
        valid_fps = 0
        for frame in self.frames[(self.fps - 10):self.fps]:
            if frame.hands[0].is_valid:
                avg[0] += frame.hands[0].palm_position[0]
                avg[1] += frame.hands[0].palm_position[1]
                avg[2] += frame.hands[0].palm_position[2]
                valid_fps += 1
        return [x / valid_fps for x in avg]

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        self.prev_frames.pop(0)
        self.prev_frames.append(self.frames[0])
        self.frames.pop(0)
        self.frames.append(controller.frame())
        if not frame.hands.is_empty:
            # Get the first hand
            hand = frame.hands[0]

            # Check if the hand has any fingers
            fingers = hand.fingers
            pitch = hand.direction.pitch * RAD_TO_DEG

            if len(fingers) == 1:
                pos = self.get_average_palm_position()
                self.backend.process_pointer(pos)

            if len(fingers) == 0 and pitch > 45:
                # Checks for scroll timer
                if 'scroll' not in self.timer.timers:
                    self.timer.start_timer('scroll')
                elif self.timer.check_timer('scroll'):
                    del self.timer.timers['scroll']
                    # Toggles scroll mode
                    self.active_modes['scroll'] = not self.active_modes['scroll']
                    print "Toggle scroll mode to %s" % self.active_modes['scroll']
            elif 'scroll' in self.timer.timers:
                del self.timer.timers['scroll']

            if self.active_modes['scroll']:
                self.backend.scroll(pitch)

            # Gestures
            gesture_found = False
            if self.check_gestures_timeout():
                for gesture in frame.gestures():
                    if gesture.type == Leap.Gesture.TYPE_SWIPE and len(fingers) in (4, 5):
                        swipe = Leap.SwipeGesture(gesture)
                        workspaces = self.backend.generate_workspace_matrix(WORKSPACE_TOTAL, WORKSPACE_COLS)
                        current_position = self.backend.get_position(workspaces, self.backend.get_current_workspace())
                        new_position = self.backend.find_new_position(workspaces, current_position, swipe.direction)
                        new_workspace = self.backend.get_workspace_by_position(workspaces, new_position)
                        self.backend.move_to_workspace(new_workspace)
                        gesture_found = True

                    if gesture.type == Leap.Gesture.TYPE_CIRCLE and len(fingers) == 4:
                        self.backend.lock_screen()
                        gesture_found = True

                    if gesture.type == Leap.Gesture.TYPE_KEY_TAP and len(fingers) == 1:
                        self.backend.click()
                        self.flush_buffer()
            if gesture_found:
                self.lock_gestures()

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
    listener = LeapListener()
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
