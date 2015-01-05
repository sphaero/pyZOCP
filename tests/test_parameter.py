import unittest
from parameter import ZOCPParameter

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

        
if __name__ == '__main__':
    ZOCPTest().test_remove()
    #unittest.main()

