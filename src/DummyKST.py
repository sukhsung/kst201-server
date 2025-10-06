from pyftdi.ftdi import Ftdi
from util import hdr_long, hdr_short, hdr_with_data
import time


USB = 0x50
HOST = 0x01



class DummyAPT:

    def __init__(self, verbose=2):
        self.verbose = verbose
        self.dev = None
        self._connecting = False

        self.requests = []
        self._closed = False

    def is_connected(self):
        return True

    def connect( self, dev_info ):
        if (self._connecting):
            return

        self.dev_info = dev_info
        
    def disconnect( self ):
        self.dev = None
        self._closed = True


    def read(self, n, attempt=1) :
        return b''

    def dev_check(self):
        return self._dev_check()
    
    def _dev_check(self):
        return False

    def write_short(self, id, p1=0, p2=0, d=USB, s=HOST):
        buf = hdr_short(id,p1,p2,d,s)
        print(f'Writing: {buf}')

    def write_long( self, id, payload,d=USB, s=HOST):
        buf = hdr_long(id,len(payload), d,s )
        print(f'Writing: {buf}')


class DummyKST(DummyAPT):
    def __init__(self,verbose=2):
        super().__init__(verbose)

        self.position = 50
        self.homed = False
                         
    
    def _dev_check(self):
        serial = self.get_serial()

        if (serial == self.dev_info['SERIAL']) :
            print( "dev_check passed")
            return True
        else :
            print( "dev_check failed")
            return False

    def get_serial(self):
        time.sleep(0.5)
        return self.dev_info['SERIAL']
    

    def get_status(self):
        status = {
            'position': self.position,
            'homing': False,
            'home' : self.homed,
            'moving': False,
            'limit' : False
        }
        time.sleep(0.5)
        return status
    
    def move_home( self ):
        self.position = 0
        self.homed = True
        time.sleep(0.5)
        return self.get_status()
    
    def move_absolute( self, target):
        self.position = target

        status = {
            'position': self.position,
            'homing': False,
            'home' : self.homed,
            'moving': False,
            'limit' : False
        }
        time.sleep(0.5)

        return status
    

    def move_relative( self, count):
        self.position += count


        status = {
            'position': self.position,
            'homing': False,
            'home' : self.homed,
            'moving': False,
            'limit' : False
        }
        time.sleep(0.5)
        return status
    