import mock

from unittest.case import TestCase
from kde_leapmotion_control import LeapListener


class LeapListenerTestCase(TestCase):
    directions = {
        'up': (0, 1, 0),
        'down': (0, -1, 0),
        'left': (-1, 0, 0),
        'right': (1, 0, 0),
    }
    workspaces = [[0, 1, 2],
                  [3, 4, 5],
                  [6, ]]

    def setUp(self):
        self.s = LeapListener()
        self.s.on_init()

    @mock.patch('backends.Backend.get_current_workspace', return_value=1)
    def test_get_workspace_position(self, mocked_get_current_workspace):
        pos = self.s.backend.get_position(self.workspaces, 5)
        self.assertEqual(pos, [2, 1])

    def test_generate_workspace_matrix(self):
        total_workspaces = 7
        workspace_columns = 3
        matrix = self.s.backend.generate_workspace_matrix(total_workspaces, workspace_columns)
        self.assertEqual(self.workspaces, matrix)

    def test_new_position_up(self):
        current_position = [1, 1]
        new_pos = self.s.backend.find_new_position(self.workspaces, current_position, self.directions['up'])
        self.assertEqual(new_pos, [1, 0])

    def test_new_position_down(self):
        current_position = [1, 0]
        new_pos = self.s.backend.find_new_position(self.workspaces, current_position, self.directions['down'])
        self.assertEqual(new_pos, [1, 1])

    def test_new_position_left(self):
        current_position = [1, 1]
        new_pos = self.s.backend.find_new_position(self.workspaces, current_position, self.directions['left'])
        self.assertEqual(new_pos, [0, 1])

    def test_new_position_right(self):
        current_position = [1, 1]
        new_pos = self.s.backend.find_new_position(self.workspaces, current_position, self.directions['right'])
        self.assertEqual(new_pos, [2, 1])

    def test_get_workspace_by_position(self):
        workspace = self.s.backend.get_workspace_by_position(self.workspaces, [2, 0])
        self.assertEqual(workspace, 2)