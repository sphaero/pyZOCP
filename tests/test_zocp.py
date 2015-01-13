import unittest
import zocp
import zmq
import time
import logging

class ZOCPTest(unittest.TestCase):
    
    def setUp(self, *args, **kwargs):
        #zl = logging.getLogger("zocp")
        #zl.setLevel(logging.DEBUG)
        self.ctx = zmq.Context()
        self.node1 = zocp.ZOCP(ctx=self.ctx)
        self.node1.set_header("X-TEST", "1")
        self.node1.set_name("node1")
        self.node2 = zocp.ZOCP(ctx=self.ctx)
        self.node2.set_header("X-TEST", "1")
        self.node2.set_name("node2")
        self.node1.start()
        self.node2.start()
        # give time for nodes to exchange
        time.sleep(1)
    # end setUp

    def tearDown(self):
        self.node1.stop()
        self.node2.stop()
        try:
            self.monitor_node.stop()
        except:
            pass
    # end tearDown

    def test_get_name(self):
        self.assertEqual("node1", self.node1.get_name())
        self.assertEqual("node2", self.node2.get_name())
    # end test_get_name

    def test_get_peers(self):
        id1 = self.node1.get_uuid()
        peers = self.node2.get_peers()

        self.assertIsInstance(peers, list)
        self.assertIn(id1, peers)
    # end test_get_peers

    def test_get_peer_address(self):
        id1 = self.node1.get_uuid()
        id2 = self.node2.get_uuid()

        self.assertIsInstance(self.node1.get_peer_address(id2), str)
        self.assertIsInstance(self.node2.get_peer_address(id1), str)
    # end test_get_peer_address

    def test_get_peer_header_value(self):
        id1 = self.node1.get_uuid()
        id2 = self.node2.get_uuid()

        self.assertEqual("1", self.node1.get_peer_header_value(id2, "X-TEST"))
        self.assertEqual("1", self.node2.get_peer_header_value(id1, "X-TEST"))
    # end test_get_peer_header_value

    def test_get_own_groups(self):
        self.node1.join("TEST")
        self.node2.join("TEST")

        # pyre works asynchronous so give some time to let changes disperse
        time.sleep(0.5)

        self.assertIn("TEST", self.node1.get_own_groups())
        self.assertIn("TEST", self.node2.get_own_groups())
    # end test_get_own_groups

    def test_get_peer_groups(self):
        self.node1.join("TEST")
        self.node2.join("TEST")

        # pyre works asynchronous so give some time to let changes disperse
        time.sleep(0.5)

        self.assertIn("TEST", self.node1.get_peer_groups())
        self.assertIn("TEST", self.node2.get_peer_groups())
    # end test_get_peer_groups

    def test_signal_subscribe(self):
        self.node1.register_float("TestEmitFloat", 1.0, 'rwe')
        self.node2.register_float("TestRecvFloat", 1.0, 'rws')
        # give time for dispersion
        self.node1.run_once()
        self.node2.run_once()
        self.node2.signal_subscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        # give time for dispersion
        time.sleep(0.5)
        self.node1.run_once()
        # subscriptions structure: {Emitter nodeID: {'EmitterID': ['Local ReceiverID']}}
        self.assertIn(0, self.node2.subscriptions[self.node1.get_uuid()][0])
        self.assertIn((self.node2.get_uuid().hex, 0), self.node1._parameter_list[0]._subscribers)
        # unsubscribe
        self.node2.signal_unsubscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        time.sleep(0.5)
        self.node1.run_once()
        self.assertNotIn(self.node1.get_uuid(), self.node2.subscriptions)
        self.assertNotIn((self.node2.get_uuid().hex, 0), self.node1._parameter_list[0]._subscribers)

    def test_signal_monitor(self):
        self.node1.register_float("TestEmitFloat", 1.0, 'rwe')
        self.node2.register_float("TestRecvFloat", 1.0, 'rws')
        self.monitor_node = zocp.ZOCP(ctx=self.ctx)
        self.monitor_node.set_name("monitor")
        self.monitor_node.start()
        # give time for dispersion
        self.node1.run_once(0)
        self.node2.run_once(0)
        self.monitor_node.run_once(0)
        # subscribe monitor to both nodes
        self.monitor_node.signal_subscribe(self.monitor_node.get_uuid(), None, self.node1.get_uuid(), None)
        self.monitor_node.signal_subscribe(self.monitor_node.get_uuid(), None, self.node2.get_uuid(), None)
        # give time for dispersion
        time.sleep(0.5)
        self.node1.run_once(0)
        self.node2.run_once(0)
        self.monitor_node.run_once(0)
        # monitor subscribers structure: [PeerId]
        self.assertIn(self.monitor_node.get_uuid(), self.node1.monitor_subscribers)
        self.assertIn(self.monitor_node.get_uuid(), self.node2.monitor_subscribers)
        # subscribe signal from node2 to node1
        self.node2.signal_subscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        time.sleep(0.5)
        self.node1.run_once(0)
        self.node2.run_once(0)
        self.monitor_node.run_once(0)
        time.sleep(0.5)
        self.node1.run_once(0)
        self.node2.run_once(0)
        self.monitor_node.run_once(0)
        # monitor should now know about subscription of node2 to node1
        for key, val in self.monitor_node.peers_capabilities[self.node1.get_uuid()].items():
            if val.get('sig_id') == 0:
                self.assertIn([self.node2.get_uuid().hex, 0], val.get('subscribers', ['subscribersnotfound']))
        # unsubscribe
        self.node2.signal_unsubscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        time.sleep(0.5)
        self.node1.run_once(0)
        self.node2.run_once(0)
        time.sleep(0.5)
        self.monitor_node.run_once(0)
        # monitor should now not now about subscription of node2 to node1
        for key, val in self.monitor_node.peers_capabilities[self.node1.get_uuid()].items():
            if val.get('sig_id') == 0:
                self.assertNotIn([self.node2.get_uuid().hex, 0], val.get('subscribers', ['subscribersnotfound']))
        self.assertNotIn(self.node1.get_uuid(), self.node2.subscriptions)
        self.assertNotIn((self.node2.get_uuid().hex, 0), self.node1._parameter_list[0]._subscribers)

    def test_emit_signal(self):
        param1 = self.node1.register_float("TestEmitFloat", 1.0, 'rwe')
        param2 = self.node2.register_float("TestRecvFloat", 1.0, 'rws')
        # give time for dispersion
        time.sleep(0.5)
        self.node1.run_once()
        self.node2.signal_subscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        # give time for dispersion
        time.sleep(0.1)
        self.node1.run_once()
        param1.set(2.0) #self.node1.emit_signal(0, 2.0)
        time.sleep(0.1)
        self.node2.run_once()
        self.assertEqual(2.0, param2.get())
        # unsubscribe
        self.node2.signal_unsubscribe(self.node2.get_uuid(), 0, self.node1.get_uuid(), 0)
        time.sleep(0.1)
        self.node1.run_once()
# end ZOCPTest

if __name__ == '__main__':
    unittest.main()
