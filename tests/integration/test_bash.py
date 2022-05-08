import json

from tests.driver import Driver


class TestIntegrationBash:
    @staticmethod
    def driver():
        with open("reple/configs/bash.json") as f:
            return Driver(json.load(f))

    def test_command(self):
        driver = self.driver()
        cmds = [
            'echo "hello world"',
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_prolog(self):
        driver = self.driver()
        cmds = [
            driver.prolog_line('echo "hello world"'),
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_both(self):
        driver = self.driver()
        cmds = [
            'echo "hello main"',
            driver.prolog_line('echo "hello prolog"'),
        ]
        assert driver.drive(cmds) == 'hello main\nhello prolog\n'

