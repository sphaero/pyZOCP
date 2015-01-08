import unittest
from parameter import ZOCPParameter, ZOCPParameterList

class ZOCPTest(unittest.TestCase):

    def test_insert(self):
        plist = ZOCPParameterList()
        mlist = []
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
        self.assertEqual(len(plist), 1)
        self.assertIs(param1, plist[param1.sig_id])
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        self.assertEqual(len(plist), 2)
        self.assertEqual(plist.index(param1), param1.sig_id)
        self.assertIs(param1, plist[param1.sig_id])
        self.assertIs(param2, plist[param2.sig_id])
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        self.assertEqual(len(plist), 3)
        self.assertIs(param1, plist[param1.sig_id])
        self.assertIs(param2, plist[param2.sig_id])
        self.assertIs(param3, plist[param3.sig_id])
        self.assertEqual(plist.index(param1), param1.sig_id)
        self.assertEqual(plist.index(param2), param2.sig_id)
        self.assertEqual(plist.index(param3), param3.sig_id)

    def test_remove(self):
        plist = ZOCPParameterList()
        mlist = []
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        self.assertEqual(len(plist), 3)
        # remove param2 and test if its id is reused
        param2.remove()
        # list length remains the same
        self.assertEqual(len(plist), 3)
        # param2's id is in the free_idx list
        self.assertIn(1, plist._free_idx)
        param4 = ZOCPParameter(None, 0.3, 'param4', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        self.assertEqual(param2.sig_id, 1)
        del param2
        # test if param4's id equals 1 (previously id of param2)
        self.assertEqual(plist.index(param4), 1)
        self.assertEqual(param4.sig_id, 1)
        param3.remove()
        self.assertEqual(len(plist), 2)
        self.assertEqual(0, len(plist._free_idx))

    def test_params_list(self):
        plist = ZOCPParameterList()
        mlist = []
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        self.assertIsInstance(plist._list, list)
        self.assertIsInstance(plist, ZOCPParameterList)
        self.assertIs(param1, plist[param1.sig_id])
        self.assertIs(param2, plist[param2.sig_id])
        self.assertIs(param3, plist[param3.sig_id])

    def test_dict_out(self):
        plist = ZOCPParameterList()
        mlist = []
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
        d = {'sig_id': 0, 'name': 'param1', 'access': 'rwes', 'typeHint': None, 'sig': 'i', 'subscribers': [], 'value': 1}
        self.assertDictEqual(param1.to_dict(), d)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', 'float', 'f', -1.0, 1.0, 0.01, params_list=plist, monitor_list=mlist)
        d = {'sig_id': 1, 'name': 'param2', 'access': 'rw', 'typeHint': 'float', 'sig': 'f', 'value': 0.1, 'min': -1.0, 'max': 1.0, 'step': 0.01}
        self.assertDictEqual(param2.to_dict(), d)

    @unittest.skip("custom JSON serializing is kind of pain in the ***")
    def test_serialize(self):
        plist = ZOCPParameterList()
        mlist = []
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
        import json
        js = json.dumps(param1)
        self.assertIsInstance(js, str)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
        js = json.dumps(plist)
        
if __name__ == '__main__':
    #ZOCPTest().test_remove()
    unittest.main()
