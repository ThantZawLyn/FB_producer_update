import unittest

from ..app.services.scheduler_service import check_tasks


class MyTestCase(unittest.TestCase):
    def test_something(self):
        check_tasks()


if __name__ == '__main__':
    unittest.main()
