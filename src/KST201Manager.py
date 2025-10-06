from APTManager import APTManager
from time import sleep
from util import hdr_long, hdr_short, hdr_with_data
from datetime import datetime
from status import parseStatus

HW_REQ_INFO = 0x0005
HW_GET_INFO = 0x0006

MOT_MOVE_HOME = 0x0443
MOT_MOVE_HOMED = 0x0444
MOT_MOVE_RELATIVE = 0x0448
MOT_SET_MOVEABSPARAMS = 0x0450
MOT_REQ_MOVEABSPARAMS = 0x0451
MOT_GET_MOVEABSPARAMS = 0x0452
MOT_MOVE_ABSOLUTE = 0x0453
MOT_MOVE_COMPLETED = 0x0464
MOT_MOVE_STOP = 0x0465
MOT_MOVE_STOPPED = 0x0466
MOT_REQ_STATUSUPDATE = 0x0480
MOT_GET_STATUSUPDATE = 0x0481

USB = 0x50
HOST = 0x01

class KST201Manager(APTManager):
    def __init__( self, verbose=2 ):
        super().__init__(verbose)

        self.GET_INFO = hdr_long( HW_GET_INFO, 84, HOST, USB)
        self.GET_STATUSUPDATE = hdr_long( MOT_GET_STATUSUPDATE, 28, HOST, USB)
        self.MOVE_HOMED = hdr_short( MOT_MOVE_HOMED,1,0,HOST,USB)
        self.MOVE_COMPLETED = hdr_long( MOT_MOVE_COMPLETED,14,HOST,USB)


    def _dev_check(self):
        serial = self.get_serial()

        if (serial == self.dev_info['SERIAL']) :
            print( "dev_check passed")
            return True
        else :
            print( "dev_check failed")
            return False
        
    def get_serial(self):
        self.purge()
        self.write_short( HW_REQ_INFO )
        sleep( 0.3 )
        resp = self.read( 6 )
        if (resp== self.GET_INFO) :
            data = self.read(84)
            serial = int.from_bytes(data[0:4], 'little', signed=False)
            print( f"SERIAL: {serial}" )
        else :
            serial = -1
            print( f"INVALID SERIAL: {serial}" )
        return serial


    def get_status(self):
        self.purge()
        self.write_short( MOT_REQ_STATUSUPDATE )
        sleep(0.3)

        stat = self.wait_until( self.GET_STATUSUPDATE, 60)
        if (stat):
            data = self.read(28)
            pos = int.from_bytes(data[2:10],'little', signed=True)
            stat = int.from_bytes(data[10:28],'little', signed=False)

            status = parseStatus(stat)
            status['position'] = pos
            print(f"STATUS: {status}")
            return status


    def move_home(self):
        self.purge()
        self.write_short( MOT_MOVE_HOME)

        homed = self.wait_until( self.MOVE_HOMED, 60)
        print( f"HOMED: {homed}")
        status = self.get_status()
        return status
    
    def move_absolute(self,target):
        self.purge()
        chan = (1).to_bytes(2,'little')
        pos = int(target).to_bytes(4,'little',signed=True)
        payload = chan+pos

        self.write_long( MOT_MOVE_ABSOLUTE,payload )
        moved = self.wait_until( self.MOVE_COMPLETED, 60)
        print( f"MOVED: {moved}")
        if moved:
            data = self.read(14)
            pos = int.from_bytes(data[2:6],'little', signed=True)
            stat = int.from_bytes(data[10:14],'little', signed=False)

            status = parseStatus(stat)
            status['position'] = pos
            print(f"STATUS: {status}")
            return status
        return moved
    
    def move_relative(self,count):
        self.purge()
        chan = (1).to_bytes(2,'little')
        pos = int(count).to_bytes(4,'little',signed=True)
        payload = chan+pos

        self.write_long( MOT_MOVE_RELATIVE,payload )
        moved = self.wait_until( self.MOVE_COMPLETED, 60)
        print( f"MOVED: {moved}")
        if moved:
            data = self.read(14)
            pos = int.from_bytes(data[2:6],'little', signed=True)
            stat = int.from_bytes(data[10:14],'little', signed=False)

            status = parseStatus(stat)
            status['position'] = pos
            print(f"STATUS: {status}")
            return status
        return moved

    def wait_until(self, header, timeout=3):
        deadline = datetime.now().timestamp()+timeout
        while ( deadline > datetime.now().timestamp()):
            resp = self.read(len(header))
            if (resp == header):
                return True
            elif (len(resp)>0):
                print( f"Wrong Header: {resp}")
            
        print("Timed out during wait_until")
        return False
        
