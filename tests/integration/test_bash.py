from tests.integration.conftest import IntegrationTest


class TestIntegrationBash(IntegrationTest):
    config_file = "reple/configs/bash.json"

    def test_command(self, driver):
        cmds = [
            'echo "hello world"',
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_prolog(self, driver):
        cmds = [
            driver.prolog_line('echo "hello world"'),
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_both(self, driver):
        cmds = [
            'echo "hello main"',
            driver.prolog_line('echo "hello prolog"'),
        ]
        assert driver.drive(cmds) == 'hello main\nhello prolog\n'

