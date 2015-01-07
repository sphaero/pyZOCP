import unittest
from parameter import ZOCPParameter, ZOCPParameterList

class ZOCPTest(unittest.TestCase):
    #def setUp(self, *args, **kwargs):

    def tearDown(self):
        ZOCPParameter.params_list.clear()
        self.assertEqual(0, len(ZOCPParameter.params_list))

    def test_insert(self):
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
        self.assertEqual(len(ZOCPParameter.params_list), 1)
        self.assertIs(param1, ZOCPParameter.params_list[param1.sig_id])
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
        self.assertEqual(len(ZOCPParameter.params_list), 2)
        self.assertEqual(ZOCPParameter.params_list.index(param1), param1.sig_id)
        self.assertIs(param1, ZOCPParameter.params_list[param1.sig_id])
        self.assertIs(param2, ZOCPParameter.params_list[param2.sig_id])
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f')
        self.assertEqual(len(ZOCPParameter.params_list), 3)
        self.assertIs(param1, ZOCPParameter.params_list[param1.sig_id])
        self.assertIs(param2, ZOCPParameter.params_list[param2.sig_id])
        self.assertIs(param3, ZOCPParameter.params_list[param3.sig_id])
        self.assertEqual(ZOCPParameter.params_list.index(param1), param1.sig_id)
        self.assertEqual(ZOCPParameter.params_list.index(param2), param2.sig_id)
        self.assertEqual(ZOCPParameter.params_list.index(param3), param3.sig_id)

    def test_remove(self):
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f')
        self.assertEqual(len(ZOCPParameter.params_list), 3)
        # remove param2 and test if its id is reused
        #print("DEL pre P2", ZOCPParameter.params_list is param2.params_list, ZOCPParameter.params_list)
        param2.remove()
        #print("DEL post P2", ZOCPParameter.params_list)
        # list length remains the same
        self.assertEqual(len(ZOCPParameter.params_list), 3)
        # param2's id is in the free_idx list
        self.assertIn(1, ZOCPParameter.params_list._free_idx)
        param4 = ZOCPParameter(None, 0.3, 'param4', 'rw', None, 'f')
        self.assertEqual(param2.sig_id, 1)
        del param2
        # test if param4's id equals 1 (previously id of param2)
        self.assertEqual(ZOCPParameter.params_list.index(param4), 1)
        self.assertEqual(param4.sig_id, 1)
        param3.remove()
        self.assertEqual(len(ZOCPParameter.params_list), 2)
        self.assertEqual(0, len(ZOCPParameter.params_list._free_idx))

    def test_params_list(self):
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
        print(param1.to_dict())
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f')
        self.assertIsInstance(ZOCPParameter.params_list._list, list)
        self.assertIsInstance(ZOCPParameter.params_list, ZOCPParameterList)
        self.assertIs(param1, ZOCPParameter.params_list[param1.sig_id])
        self.assertIs(param2, ZOCPParameter.params_list[param2.sig_id])
        self.assertIs(param3, ZOCPParameter.params_list[param3.sig_id])

    def test_dict_out(self):
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
        d = {'sig_id': 0, 'name': 'param1', 'access': 'rwes', 'typeHint': None, 'sig': 'i', 'subscribers': [], 'subscriptions': [], 'value': 1}
        self.assertDictEqual(param1.to_dict(), d)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', 'float', 'f', -1.0, 1.0, 0.01)
        print(param2)
        d = {'sig_id': 1, 'name': 'param2', 'access': 'rw', 'typeHint': 'float', 'sig': 'f', 'value': 0.1, 'min': -1.0, 'max': 1.0, 'step': 0.01}
        self.assertDictEqual(param2.to_dict(), d)

    @unittest.skip("custom JSON serializing is kind of pain in the ***")
    def test_serialize(self):
        param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
        import json
        js = json.dumps(param1)
        self.assertIsInstance(js, str)
        param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
        param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f')
        js = json.dumps(ZOCPParameter.params_list)
        
if __name__ == '__main__':
    #ZOCPTest().test_remove()
    unittest.main()

