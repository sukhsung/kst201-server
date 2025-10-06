from KST201Manager import KST201Manager

VID= 0x0403
PID =0xfaf0
SERIAL =26006611

dev_info = {'VID':VID, 'PID':PID, 'SERIAL':SERIAL}


manager = KST201Manager()

manager.connect( dev_info )

# print( manager.is_connected())

# manager.move_relative(-870000)
# manager.move_relative(2000000)
# manager.move_relative(2000000)
# manager.move_home()
manager.move_absolute(2000)
# manager.get_status()
# # manager.move_absolute(20000)
# # manager.move_absolute(200000)
# # manager.move_absolute(2000000)
# manager.move_absolute(20000000)
# manager.move_absolute(2000)