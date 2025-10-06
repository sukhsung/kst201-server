from time import time, sleep
import threading

from src.APTManager import APTManager
from src.util import hdr_long, hdr_short
from src.status import parseStatus

HW_REQ_INFO = 0x0005
HW_GET_INFO = 0x0006

MOT_MOVE_HOME = 0x0443
MOT_MOVE_HOMED = 0x0444
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
    def __init__(self, verbose=2):
        super().__init__(verbose)

        self.GET_INFO = hdr_long(HW_GET_INFO, 84, HOST, USB)
        self.GET_STATUSUPDATE = hdr_long(MOT_GET_STATUSUPDATE, 28, HOST, USB)
        self.MOVE_HOMED = hdr_short(MOT_MOVE_HOMED, 1, 0, HOST, USB)
        self.MOVE_COMPLETED = hdr_long(MOT_MOVE_COMPLETED, 14, HOST, USB)
        self.MOVE_STOPPED = hdr_long(MOT_MOVE_ABSOLUTE, 14, HOST, USB)

        # --- minimal threading bits ---
        self._motion_thread = None
        self._stop_evt = threading.Event()

        # --- out message ---
        self.out_msg = []

    # --------- Public API --------- #
    def get_info(self, emit=True):
        self.purge()
        self.write_short(HW_REQ_INFO)
        sleep(0.3)

        resp = self.wait_until(self.GET_INFO, 60)
        if resp:
            data = self.read(84)
            serial = int.from_bytes(data[0:4], "little", signed=False)
            model = data[4:12].decode().rstrip("\x00")
            print(f"MODEL: {model}, SERIAL: {serial}")
        else:
            serial = -1
            model = -1
            print(f"INVALID SERIAL: {serial}")

        resp = {"serial": serial, "model": model}
        if emit:
            self.out_msg.append(resp)
        return resp

    def get_status(self, emit=True):
        self.purge()
        self.write_short(MOT_REQ_STATUSUPDATE)
        sleep(0.3)

        resp = self.wait_until(self.GET_STATUSUPDATE, 60)
        if resp:
            data = self.read(28)
            pos = int.from_bytes(data[2:10], "little", signed=True)
            stat = int.from_bytes(data[10:28], "little", signed=False)

            status = parseStatus(stat)
            status["position"] = pos
            print(f"STATUS: {status}")
            if emit:
                self.out_msg.append(status)
            return status

    def move_home(self, timeout=60):
        """Start a move in a background thread. Returns immediately."""
        if self._motion_thread and self._motion_thread.is_alive():
            return {"moving": True, "already_in_motion": True}

        self._stop_evt.clear()
        t = threading.Thread(
            target=self._motion_worker, args=("home", timeout), daemon=True
        )
        self._motion_thread = t
        t.start()
        return {"moving": True}

    def move_absolute(self, target, timeout=60):
        """Start a move in a background thread. Returns immediately."""
        if self._motion_thread and self._motion_thread.is_alive():
            return {"moving": True, "already_in_motion": True}

        self._stop_evt.clear()
        t = threading.Thread(
            target=self._motion_worker, args=(int(target), timeout), daemon=True
        )
        self._motion_thread = t
        t.start()
        return {"moving": True}

    def move_stop(self):
        """Signal stop and send STOP now (non-blocking)."""
        self._stop_evt.set()
        try:
            self.write_short(MOT_MOVE_STOP, 1, 1)
        except Exception as e:
            with self._state_lock:
                self._state.update({"error": f"stop send failed: {e}"})
        return {"stop_sent": True}

    def motion_status(self):
        """Snapshot of current motion state (thread-safe)."""
        with self._state_lock:
            return dict(self._state)

    # --------- Workers & helpers --------- #

    def _motion_worker(self, target, timeout):
        try:
            self.purge()
            # 1) send the move
            if target == "home":
                self.write_short(MOT_MOVE_HOME, 1)
            elif isinstance(target, (int, float)):
                chan = (1).to_bytes(2, "little")
                pos = int(target).to_bytes(4, "little", signed=True)
                self.write_long(MOT_MOVE_ABSOLUTE, chan + pos)

            # 2) wait for either COMPLETED or STOPPED, with ability to be interrupted
            matched = self._wait_any_interruptible(
                [self.MOVE_HOMED, self.MOVE_COMPLETED, self.MOVE_STOPPED],
                stop_evt=self._stop_evt,
                timeout=timeout,
            )

            # 3) If wait is finished check for status
            if matched is None:
                sleep(1)
                self.get_status(emit=True)
            elif matched is MOT_MOVE_HOMED:
                self.get_status(emit=True)
            elif matched is MOT_MOVE_COMPLETED or matched is MOT_MOVE_STOPPED:
                data = self._read_exact(14, t=1.0)
                position = int.from_bytes(data[2:6], "little", signed=True)
                stat_raw = int.from_bytes(data[10:14], "little", signed=False)
                status = parseStatus(stat_raw)
                status["position"] = position
                self.out_msg.append(status)
            else:
                sleep(1)
                self.get_status(emit=True)

        except Exception as e:
            print(f"Error: {e}")

    # --------- Override abstracts
    def _dev_check(self):
        info = self.get_info(emit=False)

        if info["model"] == "KST201":
            print("dev_check passed")
            return True
        else:
            print("dev_check failed")
            return False

    def _disconnect(self):
        if self._motion_thread and self._motion_thread.is_alive():
            self._motion_thread.stop()
            self._stop_evt.clear()
