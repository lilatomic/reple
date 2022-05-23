from tests.integration.conftest import IntegrationTest


class TestIntegrationGo(IntegrationTest):
    config_file = "reple/configs/go.json"

    def test_simple(self, driver):
        r = self.replay_from_file("tests/simple.go.dat", driver)
        assert r == "Hello, World!\n25\n"