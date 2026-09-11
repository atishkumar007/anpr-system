import time
import threading
from backend.app.config import GATE_AUTO_CLOSE_SECONDS

class BarrierService:
    """
    Simulates the IoT Smart Barrier / Gate Relay behavior.
    Manages gate state, auto-closing timer, and override actions.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BarrierService, cls).__new__(cls)
                cls._instance.state = "CLOSED"  # CLOSED, OPEN, OPENING, CLOSING
                cls._instance.last_opened_at = 0.0
                cls._instance.opened_by_plate = None
                cls._instance.auto_close_seconds = GATE_AUTO_CLOSE_SECONDS
                cls._instance._timer = None
        return cls._instance

    def trigger_open(self, plate_number: str = "MANUAL_OVERRIDE"):
        with self._lock:
            self.state = "OPEN"
            self.last_opened_at = time.time()
            self.opened_by_plate = plate_number

            # Cancel previous timer if any
            if self._timer and self._timer.is_alive():
                self._timer.cancel()

            # Schedule auto-close
            self._timer = threading.Timer(self.auto_close_seconds, self._auto_close)
            self._timer.daemon = True
            self._timer.start()

            return {
                "state": self.state,
                "opened_by": self.opened_by_plate,
                "message": f"Barrier OPENED for vehicle: {plate_number}. Auto-closing in {self.auto_close_seconds}s."
            }

    def trigger_close(self):
        with self._lock:
            self.state = "CLOSED"
            self.opened_by_plate = None
            if self._timer and self._timer.is_alive():
                self._timer.cancel()
            return {"state": self.state, "message": "Barrier manually CLOSED."}

    def get_status(self):
        # Check if gate should be closed
        if self.state == "OPEN" and (time.time() - self.last_opened_at) > self.auto_close_seconds:
            self.state = "CLOSED"
            self.opened_by_plate = None

        return {
            "state": self.state,
            "last_opened_at": self.last_opened_at,
            "opened_by_plate": self.opened_by_plate
        }

    def _auto_close(self):
        with self._lock:
            self.state = "CLOSED"
            self.opened_by_plate = None
