
DEST_USB = 0x50
SRC_HOST = 0x01

def hdr_with_data(msg_id, data, d=DEST_USB, s=SRC_HOST):
    hdr = hdr_long(msg_id, len(data), d=DEST_USB, s=SRC_HOST)

    return hdr + data

def hdr_short(msg_id, p1=0, p2=0, d=DEST_USB, s=SRC_HOST):
    hdr = bytearray(6)
    hdr[0:2] = msg_id.to_bytes(2, 'little')
    hdr[2] = p1 & 0xFF
    hdr[3] = p2 & 0xFF
    hdr[4] = d & 0xFF
    hdr[5] = s & 0xFF
    return hdr


def hdr_long(msg_id, data_length, d=DEST_USB, s=SRC_HOST):
    hdr = bytearray(6)
    hdr[0:2] = msg_id.to_bytes(2, 'little')
    hdr[2:4] = data_length.to_bytes(2, 'little')
    hdr[4] = (d | 0x80) & 0xFF   # MSB set => data following
    hdr[5] = s & 0xFF
    return hdr
