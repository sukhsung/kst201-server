if __name__ == "__main__":
    import json, time
    from src.KST201Manager import KST201Manager
    from src.SocketManager import SocketManager
    from src.LEDManager import LEDManager
    import argparse, sys, socket

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dev", action="store_true", help="Dev Mode (Faux Device)"
    )
    args = parser.parse_args()

    DEV = args.dev
    if DEV:
        from src.DummyKST import DummyKST

        mgr = DummyKST()
    else:
        mgr = KST201Manager()

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        dev_info = {
            "VID": int(config["VID"], 16),
            "PID": int(config["PID"], 16),
            "SERIAL": int(config["SERIAL"]),
        }
        HOST = config["HOST"]
        PORT = int(config["PORT"])

    led = LEDManager(pin=16)
    try:
        while True:
            led.set_usb_wait()
            print("Connecting to USB device...")
            while True:
                mgr.connect(dev_info)
                if mgr.is_connected():
                    print("USB device connected.")
                    break
                print("USB device not found. Retrying in 10 seconds...")
                time.sleep(10)

            led.set_tcp_wait()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
                server_socket.bind((HOST, PORT))
                server_socket.listen()
                server_socket.settimeout(5.0)
                print(f"Server listening on {HOST}:{PORT}...")

                while True:
                    try:
                        conn, addr = server_socket.accept()
                    except socket.timeout:
                        if not mgr.is_connected():
                            print("USB device disconnected. Closing server...")
                            break
                        continue
                    except KeyboardInterrupt:
                        raise

                    led.set_connected()
                    with conn:
                        socket_manager = SocketManager(conn, mgr)
                        print(f"Connected by {addr}")
                        try:
                            while not socket_manager.closing:
                                if not mgr.is_connected():
                                    print("USB device disconnected. Closing client connection...")
                                    socket_manager.closing = True
                                    break

                                socket_manager.routine()
                        except KeyboardInterrupt:
                            raise
                        finally:
                            if mgr is not None:
                                mgr.disconnect()
                            print(f"Disconnected: {addr}")

                    if not mgr.is_connected():
                        print("USB device disconnected. Closing server...")
                        led.set_usb_wait()
                        break
                    led.set_tcp_wait()

    except KeyboardInterrupt:
        print("\nServer terminated by user.")
    finally:
        led.stop()
        sys.exit(0)
