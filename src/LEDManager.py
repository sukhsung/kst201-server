import os
import threading

_LED_PATHS = [
    "/sys/class/leds/ACT",
    "/sys/class/leds/led0",
    "/sys/class/leds/activity",
]


def _is_raspberry_pi():
    try:
        with open("/proc/device-tree/model") as f:
            return "Raspberry Pi" in f.read()
    except OSError:
        return False


def _find_led_path():
    for path in _LED_PATHS:
        if os.path.exists(path):
            return path
    return None


class LEDManager:
    """Controls the onboard ACT LED via sysfs. No-op on non-Pi hardware."""

    _PATTERNS = {
        "usb_wait": (0.1, 0.1),  # rapid
        "tcp_wait": (0.5, 0.5),  # slow
        "connected": (1, 0),     # solid on
    }

    def __init__(self):
        self._active = False
        if not _is_raspberry_pi():
            return

        led_path = _find_led_path()
        if not led_path:
            print("LED init failed: no sysfs LED path found.")
            return

        try:
            trigger_path = f"{led_path}/trigger"
            # Save the current trigger so we can restore it on exit
            with open(trigger_path) as f:
                self._orig_trigger = f.read().split("[")[-1].split("]")[0]
            with open(trigger_path, "w") as f:
                f.write("none")
            self._brightness_path = f"{led_path}/brightness"
            self._trigger_path = trigger_path
            self._write(0)
        except Exception as e:
            print(f"LED init failed: {e}")
            return

        self._state = "usb_wait"
        self._lock = threading.Lock()
        self._stop_evt = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._active = True
        print(f"LED controller active ({led_path}).")

    def set_usb_wait(self):
        self._set("usb_wait")

    def set_tcp_wait(self):
        self._set("tcp_wait")

    def set_connected(self):
        self._set("connected")

    def stop(self):
        if not self._active:
            return
        self._stop_evt.set()
        self._thread.join(timeout=1)
        self._write(0)
        try:
            with open(self._trigger_path, "w") as f:
                f.write(self._orig_trigger)
        except Exception:
            pass

    def _set(self, state):
        if not self._active:
            return
        with self._lock:
            self._state = state

    def _write(self, value):
        with open(self._brightness_path, "w") as f:
            f.write(str(value))

    def _run(self):
        while not self._stop_evt.is_set():
            with self._lock:
                state = self._state
            on_t, off_t = self._PATTERNS[state]

            self._write(1)
            if self._stop_evt.wait(on_t):
                break

            if off_t > 0:
                with self._lock:
                    still_same = self._state == state
                if still_same:
                    self._write(0)
                    self._stop_evt.wait(off_t)
