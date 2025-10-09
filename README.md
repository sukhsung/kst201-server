# kst201-server

**kst201-server** is a lightweight TCP control server for the **Thorlabs KST201** motorized stage.  
It provides a simple JSON-over-TCP protocol to interface with either real hardware (via PyFTDI) or a dummy simulator for offline testing.


## Requirements

- **Python** 3.9 or later  
- **FTDI drivers** installed (for real device use)  
- **pip** and **venv** available  

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/sukhsung/kst201-server.git
cd kst201-server
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -e .
```

---

## Configuration
Edit `config.json` to match your hardware:

```json
{
  "VID": "0x0403",
  "PID": "0xfaf0",
  "SERIAL": 26006611,
  "HOST": "0.0.0.0",
  "PORT": 48109
}
```

## For Linux, the USB needs to be added to UDEV rules
```
# /etc/udev/rules.d/11-ftdi.rules
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="faf0", GROUP="plugdev", MODE="0664"
```


## Running the Server
```bash
python kst201-server.py
```
