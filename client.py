from __future__ import print_function
import serial, io, sys

device_port = sys.argv[1]
serial = serial.Serial(device_port, 9600, rtscts=True, dsrdtr=True)
sio = io.TextIOWrapper(io.BufferedRWPair(serial, serial, 1),
                            encoding='utf-8',
                            newline='\x0d',
                            line_buffering=True)

def decode_temp(line):
    if ord(line[0]) == 2 and ord(line[1]) == 49:
        return line[2:4] + '.' + line[4:6] + ' degrees'

# read temp
sio.write(unicode("\x05\x31\x33\x31\x0d","utf-8"))
line = sio.readline()
print('[CLIENT READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))
print(decode_temp(line))

# set temp
sio.write(unicode("\x02\x31\x33\x30\x30\x30\x03\x3f\x34\x0d","utf-8"))
line = sio.readline()
print('[CLIENT READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))

# read temp
sio.write(unicode("\x05\x31\x33\x31\x0d","utf-8"))
line = sio.readline()
print('[CLIENT READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))
print(decode_temp(line))


# read internal sensor
sio.write(unicode("\x05\x32\x33\x32\x0d","utf-8"))
line = sio.readline()
print('[CLIENT READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))
print(decode_temp(line))


# read internal sensor (with intentionally wrong checksum)
sio.write(unicode("\x05\x32\x33\x31\x0d","utf-8"))
line = sio.readline()
print('[CLIENT READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))
print(decode_temp(line))

