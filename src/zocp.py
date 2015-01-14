# Z25 Orchestror Control Protocol
# Copyright (c) 2013, Stichting z25.org, All rights reserved.
# Copyright (c) 2013, Arnaud Loonstra, All rights reserved.
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

from pyre import Pyre
from parameter import ZOCPParameter, ZOCPParameterList
import json
import zmq
import uuid
import logging

logger = logging.getLogger(__name__)

def dict_get(d, keys):
    """
    returns a value from a nested dict
    keys argument must be list

    raises a KeyError exception if failed
    """
    for key in keys:
        d = d[key]
    return d

def dict_set(d, keys, value):
    """
    sets a value in a nested dict
    keys argument must be a list
    returns the new updated dict

    raises a KeyError exception if failed
    """
    for key in keys[:-1]:
        d = d[key]
    d[keys[-1]] = value

def dict_get_keys(d, keylist=""):
    for k, v in d.items():
        if isinstance(v, dict):
            # entering branch add seperator and enter
            keylist=keylist+".%s" %k
            keylist = dict_get_keys(v, keylist)
        else:
            # going back save this branch
            keylist = "%s.%s\n%s" %(keylist, k, keylist)
            #print(keylist)
    return keylist

# http://stackoverflow.com/questions/38987/how-can-i-merge-union-two-python-dictionaries-in-a-single-expression?rq=1
def dict_merge(a, b, path=None):
    """
    merges b into a, overwites a with b if equal
    """
    if not isinstance(a, dict):
        return b
    if path is None: path = []
    for key in b.keys():
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                dict_merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

class ZOCP(Pyre):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions = {}
        self.monitor_subscribers = []
        self.set_header("X-ZOCP", "1")
        self.peers_capabilities = {} # peer id : capability data
        self.capability = kwargs.get('capability', {})
        self._cur_obj = self.capability
        self._cur_obj_keys = ()
        self._parameter_list = ZOCPParameterList()
        self._running = False
        # We always join the ZOCP group
        self.join("ZOCP")
        self.poller = zmq.Poller()
        self.poller.register(self.inbox, zmq.POLLIN)

    #########################################
    # Node methods. 
    #########################################
    def set_capability(self, cap):
        """
        Set node's capability, overwites previous
        """
        logger.warning("DEPRECATED: set_capability is deprecated, capability is contructed automatically")
        self.capability = cap
        self._on_modified(data=cap)

    def get_capability(self):
        """
        Return node's capabilities
        """
        return self.capability

    def set_node_name(self, name):
        """
        Set node's name, overwites previous
        """
        # Is handled by Pyre
        logger.warning("DEPRECATED: set_node_name is deprecated, use set_name")
        self.set_name(name)

    def get_node_name(self, name):
        """
        Return node's name
        """
        # Is handled by Pyre
        logger.warning("DEPRECATED: get_node_name is deprecated, use get_name")
        return self.get_name()

    def set_node_location(self, location=[0,0,0]):
        """
        Set node's location, overwites previous
        """
        self.capability['_location'] = location
        self._on_modified(data={'_location': location})

    def set_node_orientation(self, orientation=[0,0,0]):
        """
        Set node's name, overwites previous
        """
        self.capability['_orientation'] = orientation
        self._on_modified(data={'_orientation': orientation})

    def set_node_scale(self, scale=[0,0,0]):
        """
        Set node's name, overwites previous
        """
        self.capability['_scale'] = scale
        self._on_modified(data={'scale': scale})

    def set_node_matrix(self, matrix=[[1,0,0,0],
                                      [0,1,0,0],
                                      [0,0,1,0],
                                      [0,0,0,1]]):
        """
        Set node's matrix, overwites previous
        """
        self.capability['_matrix'] = matrix
        self._on_modified(data={'_matrix':matrix})

    def set_object(self, name=None, type="Unknown"):
        """
        Create a new object on this nodes capability
        """
        if name == None:
            self._cur_obj = self.capability
            self._cur_obj_keys = ()
        if not self.capability.get('objects'):
            self.capability['objects'] = {name: {'type': type}}
        elif not self.capability['objects'].get(name):
            self.capability['objects'][name] = {'type': type}
        else:
            self.capability['objects'][name]['type'] = type
        self._cur_obj = self.capability['objects'][name]
        self._cur_obj_keys = ('objects', name)

    def _register_param(self, name, value, type_hint, signature, access='r', min=None, max=None, step=None):
        param = ZOCPParameter(self, value, name, access, type_hint, signature, min, max, step)
        param.set_object(self._cur_obj_keys)
        self._cur_obj[name] = param.to_dict()
        self._on_modified(data={name: param.to_dict()})
        return param

    def register_int(self, name, int, access='r', min=None, max=None, step=None):
        """
        Register an integer variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * int: the variable
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, int, 'int', 'I', access, min, max, step)

    def register_float(self, name, flt, access='r', min=None, max=None, step=None):
        """
        Register a float variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * int: the variable
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, flt, 'flt', 'f', access, min, max, step)

    def register_percent(self, name, pct, access='r', min=None, max=None, step=None):
        """
        Register a percentage variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * int: the variable
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, pct, 'percent', 'B', access, min, max, step)

    def register_bool(self, name, bl, access='r'):
        """
        Register an integer variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * int: the variable
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        """
        return self._register_param(name, bl, 'bool', '?', access)

    def register_string(self, name, s, access='r'):
        """
        Register a string variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * s: the variable
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        """
        return self._register_param(name, s, 'string', 's', access)

    def register_vec2f(self, name, vec2f, access='r', min=None, max=None, step=None):
        """
        Register a 2 dimensional vector variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * vec2f: A list containing two floats
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, vec2f, 'vec2f', '2f', access, min, max, step)

    def register_vec3f(self, name, vec3f, access='r', min=None, max=None, step=None):
        """
        Register a three dimensional vector variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * vec3f: A list containing three floats
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, vec3f, 'vec3f', '3f', access, min, max, step)

    def register_vec4f(self, name, vec4f, access='r', min=None, max=None, step=None):
        """
        Register a four dimensional vector variable

        Arguments are:
        * name: the name of the variable as how nodes can refer to it
        * vec4f: A list containing four floats
        * access: 'r' and/or 'w' as to if it's readable and writeable state
                  'e' if the value can be emitted and/or 's' if it can be received
        * min: minimal value
        * max: maximal value
        * step: step value used by increments and decrements
        """
        return self._register_param(name, vec4f, 'vec4f', '4f', access, min, max, step)

    #########################################
    # Node methods to peers
    #########################################
    def peer_get_capability(self, peer):
        """
        Get the capabilities of peer

        Convenience method since it's the same a calling GET on a peer with no 
        data
        """
        self.peer_get(peer, None)

    def peer_get(self, peer, keys):
        """
        Get items from peer
        """
        msg = json.dumps({'GET': keys})
        self.whisper(peer, msg.encode('utf-8'))

    def peer_set(self, peer, data):
        """
        Set items on peer
        """
        msg = json.dumps({'SET': data})
        self.whisper(peer, msg.encode('utf-8'))

    def peer_call(self, peer, method, *args):
        """
        Call method on peer
        """
        msg = json.dumps({'CALL': [method, args]})
        self.whisper(peer, msg.encode('utf-8'))

    def signal_subscribe(self, recv_peer, receiver_id, emit_peer, emitter_id):
        """
        Subscribe a receiver to an emitter

        Arguments are:
        * recv_peer: id of the receiving peer.
        * receiver_id: capability id of the receiver on the receiving peer.
                    If None, no capability on the receiving peer is
                    updated, but a on_peer_signal event is still fired.
        * emit_peer: id of the peer to subscribe to
        * emitter_id: capability id of the emitter on the peer to
                   subscribe to. If None, all capabilities will emit to
                   the receiver

        A third node can instruct two nodes to subscribe to one another
        by specifying the ids of the peers. The subscription request
        is then sent to the emitter node which in turn forwards the
        subscribtion request to the receiver node.
        """
        if recv_peer == self.get_uuid():
            # we are the receiver so register the emitter
            peer_subscriptions = {}
            if emit_peer in self.subscriptions:
                peer_subscriptions = self.subscriptions[emit_peer]
            if not emitter_id in peer_subscriptions:
                peer_subscriptions[emitter_id] = [receiver_id]
            elif not receiver_id in peer_subscriptions[emitter_id]:
                peer_subscriptions[emitter_id].append(receiver_id)
            self.subscriptions[emit_peer] = peer_subscriptions

            # check if the peer capability is known
            if receiver_id is not None:
                if receiver_id not in self.peers_capabilities:
                    self.peer_get(recv_peer, {receiver_id: {}})

        if emit_peer == self.get_uuid():
            # we are the emitter so register the receiver
            if emitter_id == None:
                self._monitor_subscribers.add(recv_peer)
            else:
                self._parameter_list[emitter_id].subscribe_receiver(recv_peer, receiver_id)

        msg = json.dumps({'SUB': [emit_peer.hex, emitter_id, recv_peer.hex, receiver_id]})
        self.whisper(emit_peer, msg.encode('utf-8'))

    def signal_unsubscribe(self, recv_peer, receiver_id, emit_peer, emitter_id):
        """
        Unsubscribe a receiver from an emitter

        Arguments are:
        * recv_peer: id of the receiving peer
        * receiver_id: capability id of the receiver on the receiving peer, or
                    None if no receiver was specified when subscribing
        * emit_peer: id of the peer to unsubscribe from
        * emitter_id3: capability name of the emitter on the peer to
                   unsubscribe from, or None if no emitter was specified
                   during subscription

        A third node can instruct two nodes to unsubscribe from one another
        by specifying the ids of the peers. The subscription request
        is then sent to the emitter node which in turn forwards the
        subscribtion request to the receiver node.
        """
        if recv_peer == self.get_uuid():
            # we are the receiver so unregister the emitter
            if (emit_peer in self.subscriptions and
                    emitter_id in self.subscriptions[emit_peer] and
                    receiver_id in self.subscriptions[emit_peer][emitter_id]):
                self.subscriptions[emit_peer][emitter_id].remove(receiver_id)
                if not any(self.subscriptions[emit_peer][emitter_id]):
                    self.subscriptions[emit_peer].pop(emitter_id)
                if not any(self.subscriptions[emit_peer]):
                    self.subscriptions.pop(emit_peer)
        if emit_peer == self.get_uuid():
            # we are the emitter so unregister the receiver
            #self._parameter_list[receiver_id].signal_unsubscribe_receiver(recv_peer, receiver_id)
            if emitter_id == None:
                self._monitor_subscribers.remove(recv_peer)
            else:
                self._parameter_list[emitter_id].unsubscribe_receiver(recv_peer, receiver_id)


        msg = json.dumps({'UNSUB': [emit_peer.hex, emitter_id, recv_peer.hex, receiver_id]})
        self.whisper(emit_peer, msg.encode('utf-8'))

    def emit_signal(self, emitter_id, data):
        """
        Update the value of the emitter and signal all subscribed receivers

        Arguments are:
        * emitter: name of the emitting capability
        * data: value
        """
        logger.warning("DEPRECATED: just set the value ( set(value) or param.value = ) on the ZOCPParameter")
        return
        self.capability[emitter]['value'] = data
        msg = json.dumps({'SIG': [emitter, data]})

        for subscriber in self.subscribers:
            if (None in self.subscribers[subscriber] or
                    emitter in self.subscribers[subscriber]):
                self.whisper(subscriber, msg.encode('utf-8'))


    #########################################
    # ZRE event methods. These can be overwritten
    #########################################
    def on_peer_enter(self, peer, name, *args, **kwargs):
        logger.debug("ZRE ENTER    : %s" %(name))

    def on_peer_exit(self, peer, name, *args, **kwargs):
        logger.debug("ZRE EXIT     : %s" %(name))

    def on_peer_join(self, peer, name, grp, *args, **kwargs):
        logger.debug("ZRE JOIN     : %s joined group %s" %(name, grp))

    def on_peer_leave(self, peer, name, grp, *args, **kwargs):
        logger.debug("ZRE LEAVE    : %s left group %s" %(name, grp))

    def on_peer_whisper(self, peer, name, data, *args, **kwargs):
        logger.debug("ZRE WHISPER  : %s whispered: %s" %(name, data))

    def on_peer_shout(self, peer, name, grp, data, *args, **kwargs):
        logger.debug("ZRE SHOUT    : %s shouted in group %s: %s" %(name, grp, data))

    #########################################
    # ZOCP event methods. These can be overwritten
    #########################################
    #def on_get(self, peer, req):
    #def on_set(self, peer, data):
    #def on_call(self, peer, req):
    #def on_subscribe(self, peer, src, dst):
    #def on_unsubscribe(self, peer, src, dst):

    def on_peer_modified(self, peer, name, data, *args, **kwargs):
        """
        Called when a peer signals that its capability tree is modified.

        peer: id of peer that made the change
        name: name of peer that made the change
        data: changed data, formatted as a partial capability dictionary, containing
              only the changed part(s) of the capability tree of the node
        """
        logger.debug("ZOCP PEER MODIFIED: %s modified %s" %(name, data))

    def on_peer_replied(self, peer, name, data, *args, **kwargs):
        logger.debug("ZOCP PEER REPLIED : %s modified %s" %(name, data))

    def on_peer_subscribed(self, peer, name, data, *args, **kwargs):
        """
        Called when a peer subscribes to an emitter on this node.

        peer: id of peer that subscribed
        name: name of peer that subscribed
        data: changed data, formatted as [emitter, receiver]
              emitter: name of the emitter on this node
              receiver: name of the receiver on the subscriber
        """
        [emit_peer, emitter, recv_peer, receiver] = data
        if emitter is None:
            logger.debug("ZOCP PEER SUBSCRIBED: %s subscribed to all emitters" %(name))
        elif receiver is None:
            logger.debug("ZOCP PEER SUBSCRIBED: %s subscribed to %s" %(name, emitter))
        else:
            logger.debug("ZOCP PEER SUBSCRIBED: %s subscribed %s to %s" %(name, receiver, emitter))

    def on_peer_unsubscribed(self, peer, name, data, *args, **kwargs):
        """
        Called when a peer unsubscribes from an emitter on this node.

        peer: id of peer that unsubscribed
        name: name of peer that unsubscribed
        data: changed data, formatted as [emitter, receiver]
              emitter: name of the emitter on this node
              receiver: name of the receiver on the subscriber
        """
        [emit_peer, emitter, recv_peer, receiver] = data
        if emitter is None:
            logger.debug("ZOCP PEER UNSUBSCRIBED: %s unsubscribed from all emitters" %(name))
        elif receiver is None:
            logger.debug("ZOCP PEER UNSUBSCRIBED: %s unsubscribed from %s" %(name, emitter))
        else:
            logger.debug("ZOCP PEER UNSUBSCRIBED: %s unsubscribed %s from %s" %(name, receiver, emitter))

    def on_peer_signaled(self, peer, name, data, *args, **kwargs):
        """
        Called when a peer signals that some of its data is modified.

        peer: id of peer whose data has been changed
        name: name of peer whose data has been changed
        data: changed data, formatted as [emitter, value]
              emitter: name of the emitter on the subscribee
              value: value of the emitter
        """
        logger.debug("ZOCP PEER SIGNALED: %s modified %s" %(name, data))

    def on_modified(self, peer, name, data, *args, **kwargs):
        """
        Called when some data is modified on this node.

        peer: id of peer that made the change
        name: name of peer that made the change
        data: changed data, formatted as a partial capability dictionary, containing
              only the changed part(s) of the capability tree of the node
        """
        if peer:
            if not name:
                name = peer.hex
            logger.debug("ZOCP modified by %s with %s" %(name, data))
        else:
            logger.debug("ZOCP modified by %s with %s" %("self", data))

    #########################################
    # Internal methods
    #########################################
    def get_message(self):
        # A message coming from a zre node contains:
        # * msg type
        # * msg peer id
        # * group (if group type)
        # * the actual message
        msg = self.recv()
        type = msg.pop(0).decode('utf-8')
        peer = uuid.UUID(bytes=msg.pop(0))
        name = msg.pop(0).decode('utf-8')
        grp=None
        if type == "ENTER":
            # This is giving conflicts when using a poller, in discussion
            #if not self.get_peer_header_value(peer, "X-ZOCP"):
            #    logger.debug("Node is not a ZOCP node")
            #    return

            if not peer in self.peers_capabilities.keys():
                self.peers_capabilities.update({peer: {}})

            self.peer_get_capability(peer)
            self.on_peer_enter(peer, name, msg)
            return

        if type == "EXIT":
            if peer in self.monitor_subscribers:
                self.monitor_subscribers.remove(peer)
            if peer in self.subscriptions:
                self.subscriptions.pop(peer)
            self.on_peer_exit(peer, name, msg)
            self.peers_capabilities.pop(peer)
            return

        if type == "JOIN":
            grp = msg.pop(0)
            self.on_peer_join(peer, name, grp, msg)
            return

        if type == "LEAVE":
            #if peer in self.subscribers:
            #    self.subscribers.pop(peer)
            #if peer in self.subscriptions:
            #    self.subscriptions.pop(peer)
            grp = msg.pop(0)
            self.on_peer_leave(peer, name, grp, msg)
            return

        if type == "SHOUT":
            grp = msg.pop(0)
            self.on_peer_shout(peer, name, grp, msg)

        elif type == "WHISPER":
            self.on_peer_whisper(peer, name, msg)

        else:
            return

        try:
            msg = json.loads(msg.pop(0).decode('utf-8'))
        except Exception as e:
            logger.error("ERROR: %s in %s, type %s" %(e, msg, type))
        else:
            for method in msg.keys():
                if method   == 'GET':
                    self._handle_GET(msg[method], peer, name, grp)
                elif method == 'SET':
                    self._handle_SET(msg[method], peer, name, grp)
                elif method == 'CALL':
                    self._handle_CALL(msg[method], peer, name, grp)
                elif method == 'SUB':
                    self._handle_SUB(msg[method], peer, name, grp)
                elif method == 'UNSUB':
                    self._handle_UNSUB(msg[method], peer, name, grp)
                elif method == 'REP':
                    self._handle_REP(msg[method], peer, name, grp)
                elif method == 'MOD':
                    self._handle_MOD(msg[method], peer, name, grp)
                elif method == 'SIG':
                    self._handle_SIG(msg[method], peer, name, grp)
                else:
                    try:
                        func = getattr(self, 'handle_'+method)
                        func(msg[method])
                    except:
                        raise Exception('No %s method on resource: %s' %(method,object))

    def _handle_GET(self, data, peer, name, grp=None):
        """
        If data is empty just return the complete capabilities object
        else fetch every item requested and return them
        """
        if not data:
            data = {'MOD': self.get_capability()}
            self.whisper(peer, json.dumps(data).encode('utf-8'))
            return
        else:
            # first is the object to retrieve from
            # second is the items list of items to retrieve
            ret = {}
            for get_item in data:
                ret[get_item] = self.capability.get(get_item)
            self.peer_set(peer, data)
            self.whisper(peer, json.dumps({ 'MOD' :ret}).encode('utf-8'))

    def _handle_SET(self, data, peer, name, grp):
        self.capability = dict_merge(self.capability, data)
        self._on_modified(data, peer, name)

    def _handle_CALL(self, data, peer, name, grp):
        return

    def _handle_SUB(self, data, peer, name, grp):
        [emit_peer, emitter_id, recv_peer, receiver_id] = data

        node_id = self.get_uuid()
        recv_peer = uuid.UUID(recv_peer)
        emit_peer = uuid.UUID(emit_peer)
        if emit_peer != node_id and recv_peer != node_id:
            # subscription requests are always initially send to the
            # emitter peer. Recv_peer can only be matched to our id if
            # a subscription to a receiver is done by the emitter.
            logger.warning("ZOCP SUB     : invalid subscription request: %s" % data)
            return

        if recv_peer != peer:
            # check if this should be forwarded (third party subscription request)
            logger.debug("ZOCP SUB     : forwarding subscription request: %s" % data)
            self.signal_subscribe(emit_peer, emitter_id, recv_peer, receiver_id)
            return

        # the sender is the receiver! This means we are the emitter
        if emitter_id == None:
            if recv_peer not in self.monitor_subscribers:
                self.monitor_subscribers.append(recv_peer)
        else:
            self._parameter_list[emitter_id].subscribe_receiver(recv_peer, receiver_id)

        self.on_peer_subscribed(peer, name, data)
        return

    def _handle_UNSUB(self, data, peer, name, grp):
        [emit_peer, emitter_id, recv_peer, receiver_id] = data

        node_id = self.get_uuid()
        recv_peer = uuid.UUID(recv_peer)
        emit_peer = uuid.UUID(emit_peer)
        if emit_peer != node_id and recv_peer != node_id:
            # unsubscription requests are always initially send to the
            # emitter peer. Recv_peer can only be matched to our id if
            # a subscription to a receiver is done by the emitter.
            logger.warning("ZOCP UNSUB   : invalid unsubscription request: %s" % data)
            return

        if recv_peer != peer:
            # check if this should be forwarded (third party unsubscription request)
            logger.debug("ZOCP UNSUB   : forwarding unsubscription request: %s" % data)
            self.signal_unsubscribe(emit_peer, emitter_id, recv_peer, receiver_id)
            return

        if emitter_id == None:
            try:
                self.monitor_subscribers.remove(recv_peer)
            except ValueError:
                pass
        else:
            self._parameter_list[emitter_id].unsubscribe_receiver(recv_peer, receiver_id)

        self.on_peer_unsubscribed(peer, name, data)

    def _handle_REP(self, data, peer, name, grp):
        return

    def _handle_MOD(self, data, peer, name, grp):
        self.peers_capabilities[peer] = dict_merge(self.peers_capabilities.get(peer), data)
        self.on_peer_modified(peer, name, data)

    def _handle_SIG(self, data, peer, name, grp):
        [emitter_id, value] = data
        if emitter_id in self.peers_capabilities[peer]:
            self.peers_capabilities[peer][emitter_id].update({'value': value})

        if peer in self.subscriptions:
            subscription = self.subscriptions[peer]
            if emitter_id in subscription:
                # propagate the signal if it changes the value of this node
                receivers = subscription[emitter_id]
                for receiver_id in receivers:
                    if receiver_id is not None and self._parameter_list[receiver_id].value != value:
                        self._parameter_list[receiver_id].value = value

            if None in subscription or emitter_id in subscription:
                self.on_peer_signaled(peer, name, data)

    def _on_modified(self, data, peer=None, name=None):
        if self._cur_obj_keys:
            # the last key in the _cur_obj_keys list equals 
            # the first in data so skip the last key
            for key in self._cur_obj_keys[::-1]:
                new_data = {}
                new_data[key] = data
                data = new_data
        self.on_modified(peer, name, data)

        if len(data):
            msg = json.dumps({ 'MOD' :data}).encode('utf-8')
            for subscriber in self.monitor_subscribers:
                # inform node that are subscribed to one or more
                # updated capabilities that they have changed
                if subscriber != peer:
                    self.whisper(subscriber, msg)

    def run_once(self, timeout=None):
        """
        Run one iteration of getting ZOCP events

        If timeout is None it will block until an
        event has been received. If 0 it will return instantly

        The timeout is in milliseconds
        """
        self._running = True
        items = dict(self.poller.poll(timeout))
        while(len(items) > 0):
            for fd, ev in items.items():
                if self.inbox == fd and ev == zmq.POLLIN:
                    self.get_message()
            # just a quick query
            items = dict(self.poller.poll(0))

    def run(self, timeout=None):
        """
        Run the ZOCP loop indefinitely
        """
        self._running = True
        while(self._running):
            try:
                items = dict(self.poller.poll(timeout))
                while(len(items) > 0):
                    for fd, ev in items.items():
                        if self.inbox == fd and ev == zmq.POLLIN:
                            self.get_message()
            except (KeyboardInterrupt, SystemExit):
                break
        self.stop()

    #def __del__(self):
    #    self.stop()

if __name__ == '__main__':

    z = ZOCP()
    z.set_node_name("ZOCP-Test")
    z.register_bool("zocpBool", True, 'rw')
    z.register_float("zocpFloat", 2.3, 'rw', 0, 5.0, 0.1)
    z.register_int('zocpInt', 10, access='rw', min=-10, max=10, step=1)
    z.register_percent('zocpPercent', 12, access='rw')
    z.run()
    z.stop()
    print("FINISH")
