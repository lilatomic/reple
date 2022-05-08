import sys
from contextlib import contextmanager
from typing import List
import io

from reple.reple import reple_from_config


@contextmanager
def capture_stdout():
    old_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = captured
    yield captured
    sys.stdout = old_stdout


class Driver:
    """Push inputs to reple. Useful for testing"""

    def __init__(self, conf, cargs='', rargs='' ):
        self.conf = conf
        self.reple = reple_from_config(conf, cargs, rargs)

    def prolog_line(self, line: str):
        return self.reple.prolog_char + line + self.reple.prolog_char

    def drive(self, cmds: List[str]):
        repl_lines = []
        prolog_lines = []
        self.in_prolog = False
        encloser_counts = [0] * len(self.reple.enclosers)

        with capture_stdout() as output:
            for line in cmds:
                self.reple.process_line(line.rstrip(), repl_lines, prolog_lines, encloser_counts)
            return output.getvalue()
