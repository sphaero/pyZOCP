from collections import MutableSequence

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
        return str(self._list)

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
    params_list = ZOCPParameterList()

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
        self.extended_meta = kwargs                 # optional extra meta data
        # get ourselves an id by inserting in the params_list
        self._sig_id = sig_id                       # the id of the parameter (needed for referencing to other nodes)
        ZOCPParameter.params_list.insert(self)
        # in case we're an emitter overwrite the set method
        if 'e' in self.access:
            self.set = self._set_emit
        self._subscribers = {}                      # dictionary containing peer receivers for emitted signals in case we're an emitter
        self._subscriptions = {}                    # dictionary containing peer emitters for receiver in case we are a signal receiver

    def _set_emit(self, value):
        """
        Set and emit value as a signal
        """ 
        self._value = value
        self._znode.emit_signal(self.sig_id, self._to_bytes)

    def set_sig_id(self, sig_id):
        if self._sig_id != None:
            logger.warning("ZOCPParameter signal id is overwritten from \
                            {0} to {1}".format(self._sig_id, sig_id))
        self._sig_id = sig_id

    def get_sig_id(self):
        return self._sig_id

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

    def signal_subscribe_emitter(self, emitter, peer, receiver):
        pass
    
    def signal_subscribe_receiver(self, receiver, peer, emitter):
        pass
        
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
        if 's' in self.access:
            d['subscriptions'] = self._subscriptions
        return d

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self.to_dict())

    def remove(self):
        # try to remove itself from the params_list
        # could already be done by clear()
        print("Removing", ZOCPParameter.params_list is self.__class__.params_list, ZOCPParameter.params_list, self.__class__.params_list)
        try:
            ZOCPParameter.params_list.remove(self)
        except ValueError:
            pass

    value = property(get, set)
    sig_id =  property(get_sig_id, set_sig_id)


if __name__ == '__main__':
    capability = []
    param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
    param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
    param3 = ZOCPParameter(None, 0.3, 'param3', 'rw', None, 'f')
    print("removing 3")
    param3.remove()
    print("adding 4&5")
    param4 = ZOCPParameter(None, 0.4, 'param4', 'rw', None, 'f')
    param5 = ZOCPParameter(None, 0.5, 'param5', 'rw', None, 'f')
    print(ZOCPParameter.params_list)
