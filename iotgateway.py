import sys
import time
import serial
from Adafruit_IO import MQTTClient

AIO_FEED_IDs = ["cong_tac_den", "cong_tac_quat", "fan_auto", "mode_light", "dat_nhiet_do"]
AIO_USERNAME = "homeless_da01"
AIO_KEY = "aio_FRcK28kFx9ylh9C7M8ArFVvbCDFc"

data_temp = "0"
auto_fan = "0"
data_limit = "31"


def autoFan(client, data_temp, auto_fan, data_limit):
    if auto_fan == "1":
        if float(data_limit) <= float(data_temp):
            # writeData("on_fan")
            client.publish("cong_tac_quat", "1")
        else:
            # writeData("off_fan")
            client.publish("cong_tac_quat", "0")

def connected(client):
    print("Ket noi thanh cong ...")
    for topic in AIO_FEED_IDs:
        client.subscribe(topic)

def subscribe(client , userdata , mid , granted_qos):
    print("Subscribe thanh cong ...")

def disconnected(client):
    print("Ngat ket noi ...")
    client.loop_stop()  # Stop the MQTT loop
    sys.exit(1)

def message(client , feed_id , payload):
    global data_temp, auto_fan, data_limit
    print("Nhan du lieu: " + payload + " , feed id: " + feed_id)
    if feed_id == "cong_tac_den":
        if payload == "1":
            writeData("on_led")
        else:
            writeData("off_led")
    if feed_id == "cong_tac_quat":
        if payload == "1":
            writeData("on_fan")
        else:
            writeData("off_fan")
    if feed_id == "mode_light":
        if payload == "1":
            writeData("on_led_warn")
        else:
            writeData("off_led_warn")
    if feed_id == "dat_nhiet_do":
        data_limit = payload
    if feed_id == "fan_auto":
        auto_fan = payload
    

def getPort():
    return "COM5"  # You need to implement this function properly

serial_port = getPort()
if serial_port:
    try:
        ser = serial.Serial(port=serial_port, baudrate=115200)
        print(ser)
    except serial.SerialException as e:
        print("Error opening serial port:", e)
        sys.exit(1)
else:
    print("No serial port found.")
    sys.exit(1)

def processData(client, data):
    global data_temp, auto_fan, data_limit
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    warning = None
    distance = None
    if splitData[0] == "TEMP":
        client.publish("cam_bien_nhiet_do", splitData[1])
        data_temp = splitData[1]
        autoFan(client, data_temp, auto_fan, data_limit)
    if splitData[2] == "HUMI":
        client.publish("cam_bien_do_am", splitData[3])
    if splitData[0] == "WARN":
        if splitData[1] == "1":
            client.publish("canh_bao", "CO NGUOI")
            if splitData[2] == "DIST":
                client.publish("cam_bien_khoang_cach", splitData[3])
        else:
            client.publish("canh_bao", "KHONG CO NGUOI")

mess = ""
def readSerial(client):
    global mess
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        mess += ser.read(bytesToRead).decode("UTF-8")
        while "!" in mess and "#" in mess:
            start = mess.find("!")
            end = mess.find("#")
            processData(client, mess[start:end + 1])
            if end == len(mess):
                mess = ""
            else:
                mess = mess[end+1:]

def writeData(data):
    ser.write(data.encode())

client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe

client.connect()
client.loop_background()

try:
    while True:
        readSerial(client)
        pass
except KeyboardInterrupt:
    print("Keyboard interrupt detected. Exiting...")
finally:
    if ser.is_open:
        ser.close()
    client.disconnect()
