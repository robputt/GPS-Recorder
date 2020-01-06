import uuid
import serial.tools.list_ports
from time import sleep
from flask import Flask
from flask import render_template
from flask import session


app = Flask(__name__)
app.secret_key = str(uuid.uuid4())


@app.route('/')
def homepage():
    return render_template('connect_device.html')


@app.route('/connect')
def connect_device():
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
        print('Device found: %s' % device_name)
        session['device'] = device_name
        return render_template('device_found.html', device_name=device_name)
    else:
        print('No device found')
        return 'No Device Found'


if __name__ == '__main__':
    app.run('0.0.0.0', 5000, threaded=True, debug=True)
