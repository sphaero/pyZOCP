class ZOCPParameter(object):
    """
    Wrapper class for parameters used through ZOCP
    """
    _id = 0                 # id counter

    def __init__(self, znode, value, name, access, type_hint, signature, min=None, max=None, step=None, *args, **kwargs):
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
        # get ourselves an id
        self.sig_id = ZOCPParameter._id             # the id of the parameter (needed for referencing to other nodes)
        ZOCPParameter._id += 1
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

    value = property(get, set)

from collections import MutableSequence
class ZOCPParameterList(MutableSequence):
    """A container for manipulating lists of parameters"""
    def __init__(self):
        """Initialize the class"""
        self._list = list()

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item by marking"""
        self._list[ii] = "*deleted*"

    def __setitem__(self, ii, val):
        self._list[ii] = val

    def __str__(self):
        return str(self._list)

    def insert(self, param):
        if param.sig_id == len(self._list):
            self._list.append(param)
        else:
            self._list[param.sig_id] = param
            
    def append(self, param):
        if param.sig_id == len(self._list):
            self._list.append(param)
        else:
            raise IndexError("ZOCPParameter cannot be appended as its ID doesn't match the length of the parameter list")
            


if __name__ == '__main__':
    capability = []
    params = ZOCPParameterList()
    param1 = ZOCPParameter(None, 1, 'param1', 'rwes', None, 'i')
    param2 = ZOCPParameter(None, 0.1, 'param2', 'rw', None, 'f')
    params.insert(param1)
    params.insert(param2)
    params.pop()
    for par in params:
        print(par)
        capability.append(par)
    import pprint
    pprint.pprint(capability)
