from tests.integration.conftest import IntegrationTest


class TestIntegrationC(IntegrationTest):
    config_file = "reple/configs/c.json"

    def test_command(self, driver):
        cmds = [
            'printf("hello world");'
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_prolog(self, driver):
        cmds = [
            driver.prolog_line('char text[] = "hello world";'),
            'printf("%s", text);'
        ]
        assert driver.drive(cmds) == 'hello world\n'
