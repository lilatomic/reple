import json

from reple.reple import DemarcatedOutputProcessor
from tests.driver import Driver


class TestOutputDemarcatedNondeterminism:
    """Tests that evaluate that nondeterminism does not impact the last output"""
    @staticmethod
    def driver():
        with open("reple/configs/bash.json") as f:
            return Driver(json.load(f))

    def test_nondeterminism(self):
        """
        This test defines a variable in the prolog and then prints it.
        It then redefines the variable to have more lines,
        which would then be printed by the previous print.
        If nondeterminism detection works, then we won't see the new value in the output
        """
        driver = self.driver()
        # force output_processor to be DemarcatedOutputProcessor
        output_processor = DemarcatedOutputProcessor(
            demarcater_template="printf '{demarcater}'",
            supported={"prolog": True, "repl": True},
        )
        driver.reple.output_processor = output_processor

        cmds = [
            driver.prolog_line("x='first'"),  # start with a 1-line definition in the prolog
            "printf $x",  # print it in the main body
            driver.prolog_line('x="${x}\\n0\\n1\\n2"'),  # redefine the value in the prolog
        ]
        assert driver.drive(cmds) == 'first\n'

        # check that output has indeed changed.
        # This digs into the internals so is fragile,
        # but I'm not sure that there's a need for a robust interface
        last_run = list(driver.reple.executions.values())[-1]
        processed_output = output_processor.undemarcate_lines(last_run)
        assert processed_output[1] == ['first\n', '0\n', '1\n', '2']
