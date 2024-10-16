from machine import RTC
import time
import socket
import struct

def set_rtc():
    host = "pool.ntp.org"
    ntp_delta = 2208988800 + 4 * 60 * 60
    ntp_query = bytearray(48)
    ntp_query[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(ntp_query, addr)
        msg = s.recv(48)
    finally:
        s.close()

    val = struct.unpack("!I", msg[40:44])[0]
    t = val - ntp_delta
    tm = time.gmtime(t)
    RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))