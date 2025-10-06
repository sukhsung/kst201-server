from KST201Manager import KST201Manager
from DummyKST import DummyKST
from SocketManager import SocketManager
import argparse, sys, socket


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="PORT")
parser.add_argument("-d", "--dev", action='store_true', help="Dev Mode (Faux Device)")
args = parser.parse_args()


HOST = "127.0.0.1"  # Localhost

PORT = int(args.port)
DEV = args.dev

if DEV:
    mgr = DummyKST()
else:
    mgr = KST201Manager()

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
            except KeyboardInterrupt:
                print("\nShutting down server...")
                break
            
            with conn:
                socket_manager = SocketManager(conn, mgr)
                print(f"Connected by {addr}")
                try:
                    while not socket_manager.closing:
                        socket_manager.routine()
                except KeyboardInterrupt:
                    print("\nInterrupted. Closing connection...")
                    break
                finally:
                    print(f"Disconnected: {addr}")


except KeyboardInterrupt:
    print("\nServer terminated by user.")
except Exception as e:
    print(f"Server error: {e}")
finally:
    sys.exit(0)
