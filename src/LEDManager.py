import threading
import time


def _is_raspberry_pi():
    try:
        with open("/proc/device-tree/model") as f:
            return "Raspberry Pi" in f.read()
    except OSError:
        return False


class LEDManager:
    """Controls a GPIO LED to reflect server state. No-op on non-Pi hardware."""

    # Blink periods in seconds: (on_time, off_time)
    _PATTERNS = {
        "usb_wait": (0.1, 0.1),   # rapid
        "tcp_wait": (0.5, 0.5),   # slow
        "connected": (1, 0),       # solid on (off_time=0 means never off)
    }

    def __init__(self, pin=16):
        self._active = False
        if not _is_raspberry_pi():
            return

        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO
            self._pin = pin
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

            self._state = "usb_wait"
            self._lock = threading.Lock()
            self._stop_evt = threading.Event()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            self._active = True
            print(f"LED controller active on GPIO{pin}.")
        except Exception as e:
            print(f"LED init failed: {e}")

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
        self._GPIO.output(self._pin, self._GPIO.LOW)
        self._GPIO.cleanup(self._pin)

    def _set(self, state):
        if not self._active:
            return
        with self._lock:
            self._state = state

    def _run(self):
        GPIO = self._GPIO
        pin = self._pin

        while not self._stop_evt.is_set():
            with self._lock:
                state = self._state
            on_t, off_t = self._PATTERNS[state]

            GPIO.output(pin, GPIO.HIGH)
            if self._stop_evt.wait(on_t):
                break

            if off_t > 0:
                # Only turn off if the state hasn't changed to something solid
                with self._lock:
                    still_same = self._state == state
                if still_same:
                    GPIO.output(pin, GPIO.LOW)
                    self._stop_evt.wait(off_t)
