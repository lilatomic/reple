import json
from abc import ABC

import pytest as pytest

from tests.driver import Driver


class IntegrationTest(ABC):

    config_file: str

    @pytest.fixture()
    def driver(self):
        with open(self.config_file) as f:
            return Driver(json.load(f))

    @staticmethod
    def replay_from_file(file, driver):
        with open(file) as f:
            lines = f.readlines()
        return driver.drive(lines)