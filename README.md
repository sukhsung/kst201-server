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
  "VID": 1240,
  "PID": 22208,
  "SERIAL": 90876543,
  "HOST": "127.0.0.1",
  "PORT": 5555
}
```


## Running the Server
```bash
python kst201-server.py
```
