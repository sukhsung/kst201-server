from pyftdi.ftdi import Ftdi
from util import hdr_long, hdr_short, hdr_with_data
import time


USB = 0x50
HOST = 0x01

HW_NO_FLASH_PROGRAMMING = 0x0018




class APTManager:

    def __init__(self, verbose=2):
        self.verbose = verbose
        self.dev = None
        self._connecting = False

        self.requests = []
        self._closed = False

    def is_connected(self):
        if (self.dev == None):
            return False
        else:
            return self.dev.is_connected
        
    def disconnect( self ):
        self.dev.close()
        self.dev = None


    def connect( self, dev_info ):
        if (self._connecting):
            return

        self.dev_info = dev_info
        self.dev = None

        try :
            # Open FTDI Connection
            self.dev = Ftdi()
            self.dev.open( vendor = dev_info['VID'], product=dev_info['PID'], serial=str(dev_info['SERIAL']))
            self.dev.set_baudrate(115200)
            self.dev.set_line_property(8, 1, 'N')

            time.sleep(0.05)
            self.dev.purge_rx_buffer()
            self.dev.purge_tx_buffer()
            time.sleep(0.05)
            self.dev.reset()

            # Hardware RTS/CTS flow control
            self.dev.set_flowctrl('')

            # Assert RTS
            self.dev.set_rts(True)

            # Run Device Check
            if (self.dev_check()):
                self.write_short(HW_NO_FLASH_PROGRAMMING)
            else:
                self.dev = None
        except:
            print( "Error during connecting")
            self.dev = None

    def read(self, n, attempt=1) :
        return self.dev.read_data_bytes(n, attempt=attempt)

    def dev_check(self):
        return self._dev_check()
    
    def _dev_check(self):
        return False

    def write_short(self, id, p1=0, p2=0, d=USB, s=HOST):
        buf = hdr_short(id,p1,p2,d,s)
        self.dev.write_data( buf )

    def write_long( self, id, payload,d=USB, s=HOST):
        buf = hdr_long(id,len(payload), d,s )
        self.dev.write_data(buf+payload)


    def purge( self ):
        self.dev.purge_buffers()