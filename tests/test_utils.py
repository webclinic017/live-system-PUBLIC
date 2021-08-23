import unittest
import src.helpers.utils as utils

# some tests redacted

class TestUtils(unittest.TestCase):
    def test_getActiveCarryContracts(self):
        self.assertEqual(utils.getActiveCarryContracts(["ZC"], "20210101 00:00:00")['ZC'][0], "ZC   DEC 21")
        self.assertEqual(utils.getActiveCarryContracts(["HG"], "20220425 00:00:00")['HG'][0], "HGN2")
        self.assertEqual(utils.getActiveCarryContracts(["HG"], "20220424 23:59:59")['HG'][0], "HGK2")
        
    def test_getRollsDue(self):
        self.assertTrue(utils.getRollsDue(["VIX"], "20211219 12:34:56"))
        self.assertFalse(utils.getRollsDue(["VIX"], "20211220 00:00:00"))
        
        self.assertTrue(utils.getRollsDue(["VIX","HG"], "20211219 00:00:00"))
        self.assertEquals(len(utils.getRollsDue(["ZC","ZW"], "20220425 00:00:00")), 2)
        self.assertEquals(len(utils.getRollsDue(["ZC","ZW"], "20220426 00:00:00")), 0)

    def test_utcOffset(self):
        import datetime as dt
        self.assertEquals(utils.utcOffset("US/Eastern", dt.datetime(2021, 8, 10)), 4)
        self.assertEquals(utils.utcOffset("US/Eastern", dt.datetime(2022, 1, 20)), 5)
        self.assertEquals(utils.utcOffset("US/Central", dt.datetime(2021, 8, 10)), 5)
        self.assertEquals(utils.utcOffset("US/Central", dt.datetime(2022, 1, 20)), 6)
        self.assertEquals(utils.utcOffset("UTC", dt.datetime(2022, 1, 20)), 0)

if __name__ == "__main__":
    unittest.main()
