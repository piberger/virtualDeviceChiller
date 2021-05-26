from __future__ import print_function
import os, serial, subprocess, time, io, re

os.environ["PYTHONUNBUFFERED"] = "1"

class ControlCode(object):
    ENQ = 0x05
    STX = 0x02
    ETX = 0x03
    ACK = 0x06
    CR  = 0x0d
    SOH = 0x01

class CommandCode(object):
    SET_TEMPERATURE = 0x31
    READ_INTERNAL_SENSOR = 0x32
    READ_EXTERNAL_SENSOR = 0x33
    READ_ALARM_STATUS = 0x34
    SET_OFFSET = 0x36
    SET_TEMPERATURE_FRAM = 0x37
    SET_OFFSET_FRAM = 0x38

class EmulatedSerialDevice(object):
    def __init__(self):

        self.temperature = 13

        print("[INFO] openening pty...")
        self.socat = subprocess.Popen(['socat', '-d', '-d', '-d', '-d', 'pty,raw,echo=0', 'pty,raw,echo=0'], stderr=subprocess.PIPE)
        time.sleep(1)

        self.ptylist = []
        while True:
            line = self.socat.stderr.readline()
            if self.socat.poll() is not None:
                break
            if line:
                pty = re.search(r"N PTY is (.+)", line)
                if pty:
                    self.ptylist.append(pty.group(1))
                    if len(self.ptylist) == 2:
                        break

        time.sleep(1)
        print(self.ptylist)

        print("[INFO] checking pty...")

        if self.socat.poll() is not None:
            print("[ERROR] socat failed.")
            exit(1)

        print("[INFO] open serial communication...")
        self.device_port = self.ptylist[0]
        self.serial = serial.Serial(self.device_port, 9600, rtscts=True, dsrdtr=True)
        self.sio    = io.TextIOWrapper(io.BufferedRWPair(self.serial, self.serial, 1),
                                       encoding='utf-8',
                                       newline='\x0d',
                                       line_buffering=True)

        print("[INFO] opened:", self.device_port, " ==> \x1b[32m", self.ptylist[1], "\x1b[0m (use this device to open serial connection)")


    def write(self, out):
        print('[WRITE]', out)
        print('[WRITE] hex=', ' '.join(hex(ord(x)) for x in out))
        self.serial.write(out)

    def read(self):
        line = self.sio.readline()
        print('[READ]', line)
        print('[READ]', 'hex=', ' '.join(hex(ord(x)) for x in line))
        return line

    def ack(self):
        self.write(chr(ControlCode.ACK) + "\x0d")

    #TODO: negative values
    def return_temperature(self, temperature):
        r = chr(ControlCode.STX) + chr(CommandCode.SET_TEMPERATURE)

        temperature_string = "%05.2f"%temperature
        if len(temperature_string) > 5:
            print("[ERROR] temperature", temperature)
            raise Exception("temperature range")

        r += temperature_string[0:2] + temperature_string[3:5]
        r += chr(ControlCode.ETX)
        s = self.computeChecksum(r)
        r += chr(48 + ((s>>4) & 0x0f))
        r += chr(48 + (s & 0x0f))
        r += "\x0d"
        self.write(r)

    #TODO: negative values
    def return_set_temperature(self):
        self.return_temperature(self.temperature)

    # TODO: negative values
    def return_internal_sensor_temperature(self):
        self.return_temperature(42.43)

    def computeChecksum(self, p):
        s = 0
        i = 1
        while(i < len(p)):
            if ord(p[i]) == ControlCode.ETX or i > len(p)-4:
                break
            s = (s + ord(p[i])) & 0xff
            i += 1
        return s

    def packet_type(self, p):
        return ord(p[0])

    def get_enq_command(self, p):
        return ord(p[1])

    def set_temperature(self, deg):
        self.temperature = deg

    def verify_checksum(self, p):
        try:
            s_expected = ((ord(p[-3]) & 0x0f) << 4) + (ord(p[-2]) & 0x0f)
            s = self.computeChecksum(p)

            print("[INFO] expected checksum:", hex(ord(p[-3])), hex(ord(p[-2])))
            print("[INFO] computed:", '0x3' + hex(s)[2], '0x3' + hex(s)[3])
            if s == s_expected:
                print("[INFO]: checksum ok!")
                return True
            else:
                print("[ERROR]: checksum error!")
                return False
        except Exception as e:
            print(e)
            raise

    def __del__(self):
        self.stop()

    def stop(self):
        self.socat.kill()
        self.out, self.err = self.socat.communicate()

dev = EmulatedSerialDevice()
while(1):
    print("reading...")
    r = dev.read()
    print("read:", r)
    dev.verify_checksum(r)

    # always ack SET commands...
    if dev.packet_type(r) == ControlCode.STX:
        dev.set_temperature(float(r[2:4] + '.' + r[4:6]))
        dev.ack()
    elif dev.packet_type(r) == ControlCode.ENQ:
        if dev.get_enq_command(r) == CommandCode.SET_TEMPERATURE:
            dev.return_set_temperature()
        if dev.get_enq_command(r) == CommandCode.READ_INTERNAL_SENSOR:
            dev.return_internal_sensor_temperature()

    time.sleep(1)


