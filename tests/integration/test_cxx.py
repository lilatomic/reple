from tests.integration.conftest import IntegrationTest


class TestIntegrationC(IntegrationTest):
    config_file = "reple/configs/cxx.json"

    def test_command(self, driver):
        cmds = [
            'std::cout << "hello world";',
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_prolog(self, driver):
        cmds = [
            driver.prolog_line('char text[] = "hello world";'),
            'std::cout << text;',
        ]
        assert driver.drive(cmds) == 'hello world\n'

    def test_multiple(self, driver):
        cmds = [
            driver.prolog_line('char text[] = "hello world";'),
            'std::cout << text;',
            'std::cout << text;',
            'std::cout << text;',
            ]
        assert driver.drive(cmds) == 'hello world\nhello world\nhello world\n'