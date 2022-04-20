from collections import defaultdict

from reple.reple import SimpleOutputProcessor


class TestSimpleOutputProcessor:
    def test_first_line(self):
        line = ["55\n"]

        executions = {
            -1: [],
            0: line
        }

        r = SimpleOutputProcessor().get_new_lines(executions, 0)
        assert r == line

    def test_has_new_lines(self):
        prev_line = ["hihello"]
        line = ["55\n"]

        executions = {
            -1: [],
            0: prev_line,
            1: prev_line + line,
        }
        r = SimpleOutputProcessor().get_new_lines(executions, 1)
        assert r == line

    def test_has_no_new_lines(self):
        line = ["55\n"]
        executions = {
            -1: [],
            0: line,
            1: line,
        }
        r = SimpleOutputProcessor().get_new_lines(executions, 1)
        assert r == []