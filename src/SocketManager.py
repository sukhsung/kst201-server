import json, socket

class SocketManager: 
    def __init__( self, connection, device_manager ):
        self.connection = connection
        connection.settimeout(1.0) 

        self.device_manager = device_manager
        self.closing = False


    def routine( self ):
        try:            
            ## Move on otherwise
            data = self.connection.recv(1024)
            if not data:
                return
            
            lines = data.decode().split('\n')

            for line in lines:
                if len(line)>0:
                    obj = json.loads(line)
                    print("Received:", obj)
                    self.handle( obj )

        except socket.timeout:
            return
        except:
            print("Error during routine, closing")
            try:
                resp = {"connected": False}
                self.send_json( resp) 
                self.device_manager.disconnect()
            finally:
                self.closing = True


    def handle( self, obj ):
        # if (obj['cmd'] == "connect"):
        #     self.device_manager.connect( obj['data'] )
        #     resp = {"connected": self.device_manager.is_connected() }
        #     self.send_json( resp)  # Echo back to client
        if (obj['cmd'] == "disconnect"):
            self.device_manager.disconnect()
            self.closing = True
        elif (obj['cmd'] == "get_info"):
            resp = self.device_manager.get_info()
            self.send_json( resp)  # Echo back to client
        elif (obj['cmd'] == "is_connected"):
            resp = {"connected": self.device_manager.is_connected()}
            self.send_json( resp)  # Echo back to client
        elif (obj['cmd'] == "get_status"):
            resp = self.device_manager.get_status()
            self.send_json( resp)  # Echo back to client
        elif (obj['cmd'] == "move_home"):
            resp = self.device_manager.move_home()
            self.send_json( resp)  # Echo back to client
        elif (obj['cmd'] == "move_absolute"):
            resp = self.device_manager.move_absolute(obj['data'])
            self.send_json( resp)  # Echo back to client
        elif (obj['cmd'] == "move_relative"):
            resp = self.device_manager.move_relative(obj['data'])
            self.send_json( resp)  # Echo back to client
        else:
            print("Invalid Command: "+obj['cmd'])
            


    def send_json( self, obj ):
        s = json.dumps(obj) + "\n" # Object in string
        print( "Sending: " + s)
        self.connection.sendall( s.encode() )


