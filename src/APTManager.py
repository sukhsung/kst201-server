from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
from src.util import hdr_long, hdr_short
from time import time, sleep
import threading


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

    def get_connected(self, emit=True):
        connected = self.is_connected()
        resp = {"connected": connected}

        if emit:
            self.out_msg.append(resp)
        return resp

    def is_connected(self):
        try:
            self.dev.modem_status()  ## DO NOT USE dev.is_connected
            return True
        except:
            return False

    def disconnect(self):
        self._disconnect()
        if self.dev != None:
            self.dev.close()
            self.dev = None

    def connect(self, dev_info):
        if self._connecting:
            return

        self.dev_info = dev_info
        self.dev = None
        UsbTools.flush_cache()

        try:
            # Open FTDI Connection
            self.dev = Ftdi()
            self.dev.open(
                vendor=dev_info["VID"],
                product=dev_info["PID"],
                serial=str(dev_info["SERIAL"]),
            )
            self.dev.set_baudrate(115200)
            self.dev.set_line_property(8, 1, "N")

            sleep(0.05)
            self.dev.purge_rx_buffer()
            self.dev.purge_tx_buffer()
            sleep(0.05)
            self.dev.reset()

            # Hardware RTS/CTS flow control
            self.dev.set_flowctrl("")

            # Assert RTS
            self.dev.set_rts(True)

            isValid = self.dev_check()
            # Run Device Check
            if isValid:
                self.write_short(HW_NO_FLASH_PROGRAMMING)
            else:
                self.dev = None
        except Exception as e:
            print("Error during connecting")
            print(f"An unexpected error occurred: {e}")
            self.dev = None

    def read(self, n, attempt=1):
        return self.dev.read_data_bytes(n, attempt=attempt)

    def dev_check(self):
        return self._dev_check()

    def _dev_check(self):
        return False

    def write_short(self, id, p1=0, p2=0, d=USB, s=HOST):
        buf = hdr_short(id, p1, p2, d, s)
        self.dev.write_data(buf)

    def write_long(self, id, payload, d=USB, s=HOST):
        buf = hdr_long(id, len(payload), d, s)
        self.dev.write_data(buf + payload)

    def purge(self):
        self.dev.purge_buffers()

        # ---- wait for any header, interruptible by stop_evt ----

    def _wait_any_interruptible(self, headers, stop_evt, timeout=3):
        ddl = time() + timeout
        need = max(len(h) for h in headers)
        bytemap = {bytes(h): h for h in headers}
        buf = bytearray()

        while time() < ddl:
            if stop_evt.is_set():
                return None  # interrupted by stop request
            chunk = self.dev.read_data_bytes(need, attempt=1)
            if chunk:
                buf.extend(chunk)
                if len(buf) > need:
                    buf[:] = buf[-need:]
                b = bytes(buf)
                for k, original in bytemap.items():
                    if len(b) >= len(k) and b[-len(k) :] == k:
                        return original
            else:
                sleep(0.01)
        return None

    # ---- simpler non-interruptible variant ----
    def wait_until(self, header, timeout=3):
        resp = self._wait_any([header], timeout=timeout)

        return resp == header

    def _wait_any(self, headers, timeout=3):
        dummy = threading.Event()
        return self._wait_any_interruptible(headers, dummy, timeout)

    # ---- accumulate exactly n bytes (short helper) ----
    def _read_exact(self, n, t=1.0):
        ddl = time() + t
        buf = bytearray()
        while time() < ddl and len(buf) < n:
            chunk = self.dev.read_data_bytes(n - len(buf), attempt=1)
            if chunk:
                buf.extend(chunk)
            else:
                sleep(0.01)
        return bytes(buf) if len(buf) == n else None
