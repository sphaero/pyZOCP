import logging
import json
import uuid
from collections import MutableSequence

logger = logging.getLogger(__name__)

class ZOCPParameterList(MutableSequence):
    """
    A container for manipulating lists of parameters
    
    Perhaps we should use weakrefs:
    https://docs.python.org/2/library/weakref.html#weak-reference-objects
    
    It's also easier to just use a dict but we need this logic in C as
    well
    """
    def __init__(self):
        """Initialize the class"""
        self._list = list()
        self._free_idx = list()           # list of free indexes

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item by marking"""
        if ii >= len(self._list):
            raise IndexError("Index {0} to remove is beyond list boundary".format(ii))
        # ii can be negative so convert to real index
        idx = ii % len(self._list)
        print("deleting idx {0}".format(idx))
        if idx == len(self._list)-1:
            self._list.pop()
            return
        self._list[idx] = None
        self._free_idx.append(idx)

    def __setitem__(self, ii, val):
        self._list[ii] = val

    def __str__(self):
        return "ZOCPParameterList:"+ str(self._list)

    def __repr__(self):
        return self._list

    def insert(self, param):
        if param.sig_id == None:
            # find a free spot in the list
            try:
                param.sig_id = self._free_idx.pop(0)
            except IndexError:
                param.sig_id = len(self._list)
                self._list.append(param)
            else:
                print("reusing id", param.sig_id, )
                self._list[param.sig_id] = param
        elif param.sig_id == len(self._list):
            self._list.append(param)
        else:
            self._list[param.sig_id] = param

    def append(self, param):
        raise NotImplemented("Append is not implemented, use insert")

    def clear(self):
        # http://bugs.python.org/issue11388
        try:
            while True:
                param = self.pop()
                param.sig_id = None
        except IndexError:
            pass


class ZOCPParameter(object):
    """
    Wrapper class for parameters used through ZOCP
    """

    def __init__(self, znode, value, name, access, type_hint, signature, min=None, max=None, step=None, sig_id=None, *args, **kwargs):
        self._value = value
        # init meta data
        self._znode = znode                         # reference to the ZOCPNode instance
        self.name = name                            # name of the parameter
        self.min = min                              # minimum value of the parameter (optional)
        self.max = max                              # maximum value of the parameter (optional)
        self.step = step
        self.access = access                        # description of access methods (Read,Write,signal Emitter,Signal receiver)
        self.type_hint = type_hint                  # a hint of the type of data
        self.signature = signature                  # signature describing the parameter in memory
        self._subscribers = []                      # list of peer receivers for emitted signals in case we're an emitter
        self._sig_id = sig_id                       # the id of the parameter (needed for referencing to other nodes)

        # get the params_list and monitor_list before we get extra meta data!
        self._params_list = kwargs.pop('params_list', None)
        self._monitor_subscribers = kwargs.pop("monitor_list", None)

        self.extended_meta = kwargs                 # optional extra meta data

        # in case we're an emitter overwrite the set method
        if 'e' in self.access:
            self.set = self._set_emit

        if self._params_list == None:
            self._params_list = self._znode._parameter_list
        if self._monitor_subscribers == None:
            self._monitor_subscribers = self._znode.monitor_subscribers
        # get ourselves an sig_id by inserting in the params_list
        self._params_list.insert(self)

    def _set_emit(self, value):
        """
        Set and emit value as a signal
        """ 
        self._value = value
        msg = json.dumps({'SIG': [self.sig_id, self._value]})
        for peer, recv_id in self._subscribers:
            self._znode.whisper(uuid.UUID(peer), msg.encode('utf-8'))
        for peer in self._monitor_subscribers:
            self._znode.whisper(peer, msg.encode('utf-8'))

    def set_sig_id(self, sig_id):
        if self._sig_id != None and sig_id != None:
            logger.warning("ZOCPParameter signal id is overwritten from"\
                           +" {0} to {1}".format(self._sig_id, sig_id))
        self._sig_id = sig_id

    def get_sig_id(self):
        return self._sig_id

    def set_object(obj):
        """
        Set object path
        
        we need this in order to find ourselves in the capability tree
        """
        self._object = obj

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

    def subscribe_receiver(self, recv_peer, receiver_id):
        # update subscribers list
        # TODO: I'm not sure we need to register the receiver_id???
        subscriber = (recv_peer.hex, receiver_id)
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            self._znode._on_modified(data={self.sig_id: {"subscribers": self._subscribers}})

    def unsubscribe_receiver(self, recv_peer, receiver_id):
        # update subscribers list
        # TODO: I'm not sure we need to register the receiver_id???
        subscriber = (recv_peer.hex, receiver_id)
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
            data=zocp.make_dict(self._object, {"subscribers": self._subscribers})
            self._znode._on_modified(data=data)

    def _to_bytes(self):
        """
        converts value to an array of bytes
        
        ref: https://docs.python.org/2/library/stdtypes.html#memoryview
        """
        return struct.pack(self.signature, self.value)
    
    def to_dict(self):
        """
        Converts this parameter to a representing dictionary
        """
        d = self.extended_meta
        d['name'] = self.name
        d['value'] = self._value
        if self.min:
            d['min'] = self.min
        if self.max:
            d['max'] = self.max
        if self.step:
            d['step'] = self.step
        d['access'] = self.access
        d['typeHint'] = self.type_hint
        d['sig'] = self.signature
        d['sig_id'] = self.sig_id
        if 'e' in self.access:
            d['subscribers'] = self._subscribers
        return d

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return "ZOCPParameter({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})"\
        .format("znode", self._value, self.name, self.access, self.type_hint, self.signature, self.min, self.max, self.step, self.sig_id)
        #return self.to_dict().__repr__()

    def __dict__(self):
        return to_dict()

    def remove(self):
        # try to remove itself from the params_list
        # could already be done by clear()
        try:
            self._params_list.remove(self)
        except ValueError:
            pass

    value = property(get, set)
    sig_id =  property(get_sig_id, set_sig_id)


if __name__ == '__main__':
    plist = ZOCPParameterList()
    mlist = []
    param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i', params_list=plist, monitor_list=mlist)
    param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
    param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
    print("removing 3")
    param3.remove()
    print("adding 4&5")
    param4 = ZOCPParameter(None, 0.4, 'param4', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
    param5 = ZOCPParameter(None, 0.5, 'param5', 'rw', None, 'f', params_list=plist, monitor_list=mlist)
    print(plist)
