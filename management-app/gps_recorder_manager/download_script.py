import json
import csv
import pytz
import datetime
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
    conn = Serial(device, 38400)
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
    to_convert = []
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
            csv_name = '%s.csv' % file
            f = open(csv_name, 'a')
            f.write(data)
            f.close()
            to_convert.append(csv_name)
        count += 1

    count = 1
    for file in to_convert:
        print("Converting file %s of %s to GPX format" % (count, len(to_convert)))
        gpx_name = '%s.gpx' % file.replace('.csv', '')

        csv_file = open(file, 'r')
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        valid_date = None
        for row in csv_reader:
            date = row[0]
            try:
                valid_date = datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
                valid_date.replace(tzinfo=pytz.UTC)
                if valid_date.year < 2019:
                    raise Exception("Date is too old.")
                break
            except:
                pass
        csv_file.close()

        if not valid_date:
            print("Error processing file")
            valid_date = datetime.datetime.utcnow()

        gpx_file = open(gpx_name, 'a')
        gpx_file.write('''<?xml version="1.0" encoding="UTF-8"?>''')
        gpx_file.write('''<gpx creator="GPS Recorder" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1" xmlns="http://www.topografix.com/GPX/1/1">''')
        gpx_file.write('''<metadata>''')
        formatted_start_date = '%sZ' % valid_date.isoformat()
        gpx_file.write('''<time>%s</time>''' % formatted_start_date)
        gpx_file.write('''</metadata>''')
        gpx_file.write('''<trk>''')
        gpx_file.write('''<name>GPS Recorder Export</name><type>1</type>''')
        gpx_file.write('''<trkseg>''')

        csv_file = open(file, 'r')
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:
            date = row[0]
            try:
                valid_date = datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
                valid_date.replace(tzinfo=pytz.UTC)
                if valid_date.year < 2019:
                    raise Exception("Date is too old.")
                if row[1].strip() == 'null' or row[2].strip() == 'null' or row[3].strip() == 'null':
                    raise Exception("Bad values")
                gpx_file.write('''<trkpt lat="%s" lon="%s">''' % (row[1].strip(), row[2].strip()))
                gpx_file.write('''<ele>%s</ele>''' % row[3].strip())
                gpx_file.write('''<time>%sZ</time>''' % valid_date.isoformat())
                gpx_file.write('''</trkpt>''')
            except Exception as err:
                print("Hit exception: %s" % str(err))

        gpx_file.write('''</trkseg>''')
        gpx_file.write('''</trk>''')
        gpx_file.write('''</gpx>''')
        gpx_file.close()
        count += 1

    conn.close()


if __name__ == '__main__':
    main()
