from collections import defaultdict

from reple.reple import SimpleOutputProcessor, DemarcatedOutputProcessor


class TestSimpleOutputProcessor:
    def test_first_line(self):
        line = ['55\n']

        executions = {
            -1: [],
            0: line
        }

        r = SimpleOutputProcessor().get_new_lines(executions, 0)
        assert r == line

    def test_has_new_lines(self):
        prev_line = ['hihello']
        line = ['55\n']

        executions = {
            -1: [],
            0: prev_line,
            1: prev_line + line,
        }
        r = SimpleOutputProcessor().get_new_lines(executions, 1)
        assert r == line

    def test_has_no_new_lines(self):
        line = ['55\n']
        executions = {
            -1: [],
            0: line,
            1: line,
        }
        r = SimpleOutputProcessor().get_new_lines(executions, 1)
        assert r == []


class TestLineDemarcater:
    demarcater_template = 'print("{demarcater}")'

    def test_demarcate_lines(self):
        lines = ['print(0)', 'print(1)']
        r = DemarcatedOutputProcessor(self.demarcater_template).demarcate_lines(lines, 4)
        assert r == ['print("start:¶4")', 'print(0)', 'print(1)', 'print("end:¶4")']

    def test_undemarcate_lines(self):
        output = ['start:¶4\n', '0\n', '1\n', 'end:¶4\n']
        r = DemarcatedOutputProcessor(self.demarcater_template).undemarcate_lines(output)
        assert r == {
            4: ['0\n', '1\n']
        }

    def test_get_new_lines(self):
        executions = {
            0: ['start:¶0\n', '0\n', 'end:¶1\n'],
            1: ['start:¶0\n', '0\n', 'end:¶0\n', 'start:¶1\n', '1\n', 'end:¶1\n'],
        }
        r = DemarcatedOutputProcessor(self.demarcater_template).get_new_lines(executions, 1)
        assert r == ['1\n']
        