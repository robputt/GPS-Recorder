import json
import serial.tools.list_ports
from serial import Serial
from time import sleep


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def get_device():
    existing_ports = []
    device_name = None

    for port in list(serial.tools.list_ports.comports()):
        existing_ports.append(port.device)

    for x in range(0, 30):
        print('Searching for device')
        new_ports = []
        for port in list(serial.tools.list_ports.comports()):
            new_ports.append(port.device)
        diff = list(set(new_ports) - set(existing_ports))
        if len(diff) == 1:
            device_name = diff[0]
        else:
            sleep(1)

    if device_name:
        print("Device Found: %s" % device_name)
        return device_name
    else:
        raise Exception("No device found")


def main():
    device = get_device()
    conn = Serial(device)
    conn.read_until(b'Waiting 30 seconds for computer connection to enter download mode...')
    conn.write(b'1')
    conn.read_until(b'OK')
    conn.write(b'ls')
    ls = conn.read_until(b'OK')
    ls = ls.decode('utf-8')
    ls = ls.replace('OK', '')
    ls = ls.strip()
    ls = rreplace(ls, ',', '', 1)
    ls = json.loads(ls)

    count = 1
    for file in ls:
        print("Downloading file %s of %s" % (count, len(ls)))
        if not file.startswith('.'):
            conn.write(b'read')
            conn.read_until(b'READ')
            conn.write(('%s' % file).encode('utf-8'))
            data = conn.read_until(b'OK')
            data = data.decode('utf-8')
            data = data.replace('OK', '')
            data = data.rstrip()
            data = data.lstrip()
            f = open('%s.csv' % file, 'a')
            f.write(data)
            f.close()
        count += 1

    conn.close()


if __name__ == '__main__':
    main()
