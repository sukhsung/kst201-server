import json, socket


class SocketManager:
    def __init__(self, connection, device_manager):
        self.connection = connection
        connection.settimeout(0.3)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

        self.device_manager = device_manager
        self.closing = False

    def routine(self):
        try:
            # Check for outward message from device
            if len(self.device_manager.out_msg) > 0:
                msg = self.device_manager.out_msg.pop(0)
                self.send_json(msg)

            data = self.connection.recv(1024)
            if not data:
                return

            lines = data.decode().split("\n")

            for line in lines:
                if len(line) > 0:
                    obj = json.loads(line)
                    print("Received:", obj)
                    self.handle(obj)

        except socket.timeout:
            return
        except Exception as e:
            print(e)
            print("Error during routine, closing")
            try:
                resp = {"connected": False}
                self.send_json(resp)
                self.device_manager.disconnect()
            finally:
                self.closing = True

    def handle(self, obj):
        if obj["cmd"] == "disconnect":
            self.device_manager.disconnect()
            self.closing = True
        elif obj["cmd"] == "get_info":
            self.device_manager.get_info()
        elif obj["cmd"] == "is_connected":
            resp = self.device_manager.get_connected(emit=False)
            self.send_json(resp)
        elif obj["cmd"] == "get_status":
            self.device_manager.get_status()
        elif obj["cmd"] == "move_home":
            self.device_manager.move_home()
        elif obj["cmd"] == "move_absolute":
            self.device_manager.move_absolute(obj["data"])
            print("move started")
        elif obj["cmd"] == "move_relative":
            self.device_manager.move_relative(obj["data"])
        elif obj["cmd"] == "move_stop":
            self.device_manager.move_stop()
        else:
            print("Invalid Command: " + obj["cmd"])

    def send_json(self, obj):
        s = json.dumps(obj) + "\n"  # Object in string
        print("Sending: " + s)
        self.connection.sendall(s.encode())
