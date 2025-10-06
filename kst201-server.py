if __name__ == "__main__":
    import json
    from src.KST201Manager import KST201Manager
    from src.SocketManager import SocketManager
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

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            print(f"Server listening on {HOST}:{PORT}...")

            while True:
                try:
                    conn, addr = server_socket.accept()
                    mgr.connect(dev_info)
                except KeyboardInterrupt:
                    print("\nShutting down server...")
                    break

                with conn:
                    socket_manager = SocketManager(conn, mgr)
                    print(f"Connected by {addr}")
                    try:
                        while not socket_manager.closing:
                            ## Check for Connection
                            if not mgr.is_connected():
                                socket_manager.closing = True
                                break

                            socket_manager.routine()
                    except KeyboardInterrupt:
                        print("\nInterrupted. Closing connection...")
                        break
                    finally:
                        if mgr is not None:
                            mgr.disconnect()
                        print(f"Disconnected: {addr}")

    except KeyboardInterrupt:
        print("\nServer terminated by user.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        sys.exit(0)
