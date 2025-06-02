import unittest
from tests import test_remotedict_server
from tests import test_expiring_remotedict_server
from tests import test_persistent_remotedict_server

if __name__ == "__main__":
    suite1 = unittest.defaultTestLoader.loadTestsFromModule(test_remotedict_server)
    suite2 = unittest.defaultTestLoader.loadTestsFromModule(test_expiring_remotedict_server)
    suite3 = unittest.defaultTestLoader.loadTestsFromModule(test_persistent_remotedict_server)
    all_tests = unittest.TestSuite([suite1, suite2, suite3])
    unittest.TextTestRunner().run(all_tests)
