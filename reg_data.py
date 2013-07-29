# A basic set of container classes for register data
# Gordon McGregor gordon.mcgregor@verilab.com

from json import dump, load
from pprint import pprint

__version__ = '0.1a'

class __register_base(object):
    def __init__(self, parent, name='undefined'):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.__str__().__hash__()

    def __dir__(self):
        return self.children()

    def __iter__(self):
        for child in self.children():
            yield self.__get_child__(child)
   
    def __repr__(self):
        return str(self.children())

    def show(self, verbose = False):
        info = self.__dir__()
        info.sort()
        pprint(info)

    def children(self):
        return self.keys()

    def keys(self):
        raise RegisterError("Implement keys")

def load_map(map_name):
    register_data = load(open(map_name))
    return RegisterMap(register_data, map_name.split(".")[0])

class RegisterError(Exception):
    def __init__(self, value):
        self.value = value
        Exception.__init__(self)
                
    def __str__(self):
        return repr(self.value)

class RegisterMap:
    def __init__(self, register_data, name='undefined'):
        self.register_data = register_data
        self.name = name

    def __dir__(self):
        return self.register_blocks()

    def __iter__(self):
        for block in self.register_blocks():
            yield self.__getattr__(block)

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.__str__().__hash__()

    def __repr__(self):
        return str(self.register_blocks())

    def __getattr__(self, attr):
        if (attr):
            if self.is_register_block(attr):
                return RegisterBlock(self, attr)
            elif self.is_memory(attr):
                return Memory(self, attr)
        else:
            raise RegisterError("Block is unknown "+ attr)

    def is_register_block(self, name):
        try:
            return self.register_data['default_map'][name]['region_type'] == 'register_block'
        except:
            return False

    def is_memory(self, name):
        try:
            return self.register_data['default_map'][name]['region_type'] == 'memory'
        except:
            return False

    def register_blocks(self):
        return self.keys()

    def keys(self):
        keys = self.register_data['default_map'].keys()
        keys.sort()
        return keys


class RegisterBlock(__register_base):

    def __init__(self, parent, name = 'undefined'):
        self.parent = parent
        self.register_block_type = self.parent.register_data['default_map'][name]['register_block_type']
        self.name = name

    def __dir__(self):
        return self.registers()
    
    def __iter__(self):
        for i in self.registers(numerical_sort=True):
            yield self.__get_register(i)

    def __get_register(self, name):
        return Register(self, self.parent, name)

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.__str__().__hash__()

    def __repr__(self):
        return str(self.registers())
        
    def __getattr__(self, attr):   
        if self.__class__.__dict__.has_key('is_' + attr):
            return getattr(self, 'is_' + attr)()
        if self.__class__.__dict__.has_key('get_' + attr):
            return getattr(self, 'get_' + attr)()      
        return self.__get_register(attr)
        
    def get_base(self):
        try:
            return self.parent.register_data['default_map'][self.name]['base']
        except(KeyError):
            if not self.parent.register_data(self.name):
                raise RegisterError('unknown register block: ' + self.name)
            else:
                raise RegisterError("register block " + self.name + " has no base entry")
 
    def is_memory(self):
        return False
   
    def is_register_block(self):
        return True

    def registers(self, numerical_sort=False):
        try:    
            data = self.parent.register_data['register_blocks'][self.register_block_type]['registers'].keys()
  #          if numerical_sort:
  #              data.sort(cmp = lambda x,y: cmp( Register(self, self.parent, x).get_address(), Register(self, self.parent, y).get_address()) )
  #          else:
  #              data.sort()
            return data
        except(KeyError):
            raise RegisterError('unknown register block: ' + self.name)
        

    def keys(self):
        try:
            return self.parent.register_data['register_blocks'][self.register_block_type].keys()
        except(KeyError):
            raise RegisterError('unknown register_block: ' + self.name)
           
        
class Register(__register_base):

    def __init__(self, parent=None, register_map=None, name='undefined'):
        self.parent = parent
        self.register_map = register_map
        self.name = name
        
    def __dir__(self):
        return self.fields()
    
    def __iter__(self):
        for i in self.fields():
            yield self.__get_field(i)

    def fields(self):
        data = self.register_map.register_data['register_blocks'][self.parent.register_block_type]['registers'][self.name]['fields'].keys()
   #     data.sort(cmp = lambda x,y: cmp( Field(self, self.parent, self.register_map, x).lsb, Field(self, self.parent, self.register_map, y).lsb) )
        return data
    
    def __str__(self):
        return '.'.join((self.register_map.name, self.parent.name, self.name)) 

    def __hash__(self):
        return self.__str__().__hash__()
    
    def __eq__(self, other):
      return self.__str__() == other.__str__()

    def __repr__(self):
        return str(self.fields())
        
    def __getattr__(self, attr):

        # basic dispatcher logic - check for get_'attr'() and is_'attr'() methods
        if self.__class__.__dict__.has_key('get_' + attr):
            return getattr(self, 'get_' + attr)()

        if self.__class__.__dict__.has_key('is_' + attr):
            return getattr(self, 'is_' + attr)()
        
        if attr == 'desc':
            try:
                return self.reg_map_entry['desc'][0]
            except(KeyError):
                raise RegisterError('unknown register: ' + self.name)        
            
        return self.__get_field(attr)
    
    def get_base(self):
        return self.parent.get_base()


    def __get_field(self, name):
        if name in self.fields():
            return Field(self, self.parent, self.register_map, name)  
        else:
            raise RegisterError(self.name + ' register does not have a field ' + name)      
        
    def get_offset(self):
        try:
            offset = self.register_map.register_data['register_blocks'][self.register_block.register_block_type][self.name]['offset']
            return offset
        except(KeyError):
            raise RegisterError('unknown register: ' + self.name)

    def get_length(self):
        return 4    # hack for now - should calculate?
        
    def is_writeable(self):
        type = self.get_type()
        if    type.find("RW") != -1 or type.find("WO") != -1: # anything other than RO is writeable (RW, WOC, WOT)
            return True
        else:
            return False
 
    def is_readable(self):
        type = self.get_type()
        if type.find("WO") != -1:
            return False
        else:
            return True    
        
    def is_memory(self):
        return False
    
    def is_register(self):
        return True
        
    def get_addr(self):
        return self.parent.get_base() + self.get_offset()


class Memory(__register_base):   
    def __init__(self, parent, name = 'undefined'):
        self.parent = parent
        self.name = name
 

    def __str__(self):
        return self.name

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration
                
    def __hash__(self):
        return self.__str__().__hash__()

    def __repr__(self):
        return self.name
    

    def __getattr__(self, attr):
        if self.__class__.__dict__.has_key('get_' + attr):
            return getattr(self, 'get_' + attr)()

        if self.__class__.__dict__.has_key('is_' + attr):
            return getattr(self, 'is_' + attr)()
 
        try:
            return self.parent.register_data[self.name][attr]
        except(KeyError):
            raise RegisterError('unknown region: ' + self.name)   
    
    def is_memory(self):
        return True
    
    def is_register_block(self):
        return False
    
    def is_register(self):
        return False

    def get_base(self):
        """Find the base address for this memory region"""
        try:
            return self.parent.register_data[self.name]['base']
        except(KeyError):
            if not self.parent.register_data.has_key(self.name):
                raise RegisterError('unknown region: ' + self.name)
            else:
                raise RegisterError("memory " + self.name + " has no base entry")
        

#             return Field(self, self.parent, self.register_map, name)  

class Field(__register_base):
    def __init__(self, parent = None, register_block = None, register_map = None, name = 'undefined'):
        self.parent = parent
        self.register_block = register_block
        self.register_map = register_map
        self.name = name

    def __str__(self):
        return '.'.join((self.register_map.name, self.register_block.name, self.parent.name, self.name)) 
    
    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
      return self.__str__() == other.__str__()

    def __repr__(self):
        return str(self.__str__())
        
    def __getattr__(self, attr):
        if self.__class__.__dict__.has_key('get_' + attr):
            return getattr(self, 'get_' + attr)()
        if self.__class__.__dict__.has_key('is_' + attr):
            return getattr(self, 'is_' + attr)()
        try:
            return self.get_key(attr)
        except(KeyError):
            raise RegisterError('unknown field: ' + self.name + ' attr: ' + attr)        
    
    def get_valid(self):
        try:
            ranges = self.get_key('valid')
        except(KeyError):
            ranges = 'all'
        
        if ranges is 'all':
            return ('all', 'all')
        else:
            return (min(ranges), max(ranges))
    
    def get_lsb(self):
        return self.get_key('lsb')
    
    def get_width_format_string(self):
        return "0x%%0%dx" % ( (self.get_key('width')+3)/4 )
    
    def get_key(self, attr='lsb'):       
        return self.register_map.register_data['register_blocks'][self.register_block.register_block_type]['registers'][self.parent.name]['fields'][self.name][attr]
    
    def get_mask(self):
        width = self.get_key('width')
        lsb = self.get_key('lsb')
        
        mask = 0
        for bit in xrange(width):
            mask |= (1 << bit)
        mask = mask << lsb
        return mask

    def extract_value(self, value = 0xff):
        return (value & self.get_mask()) >> self.get_lsb()

if __name__ == '__main__':
    print 'test code here'
    register_map = load_map("test_data.json")
    block = register_map.bank1
    register = block.status
    field = block.status.field1

    for block in register_map:
        if block.is_register_block():
            for register in block:
                for field in register:
                    print field
        else:
            print block, "is memory"



