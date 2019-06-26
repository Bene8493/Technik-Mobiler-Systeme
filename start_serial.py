import time
import sys
import serial
from thread import start_new_thread
from random import randint

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
ser.isOpen()
ser.write("AT+ADDR=" + sys.argv[1] + "\r\n")
time.sleep(0.5)
ser.write("AT+CFG=433000000,20,6,10,1,1,0,0,0,0,3000,8,4\r\n")
input=1

currDest = ''
received = []
knownAddr = ["FFFF"]

waitingForOk = False
ok = False

def getOut():
    out = ''
    while not out.endswith("\r\n"):
        if ser.inWaiting() == 0:
            time.sleep(0.1)
        else:
            out += ser.read(1)
    return out

def receive():
    global input
    while input != 'exit':
        out = getOut()
        print(out)
        received.append(out)
        
def processReceived():
    global ok
    global input
    global knownAddr
    while input != "exit":
        if len(received) == 0:
            time.sleep(0.1)
        else:
            cmd = received.pop(0)
            if cmd.endswith("AT,OK\r\n"):
                ok = True
            elif cmd.endswith("RTI\r\n"):
                addr = cmd.split(",")[1]
                if addr not in knownAddr:
                    knownAddr.append(addr)
                    print("Found address " + addr)
                
def waitForOk():
    global ok
    while not ok:
        time.sleep(0.1)

def sendAndWaitForOk(s):
    global waitingForOk
    global ok
    while waitingForOk:
        time.sleep(0.1)
    waitingForOk = True
    ser.write(s)
    waitForOk()
    ok = False
    waitingForOk = False
            
def sendRti():
    global currDest
    while 1:
        if currDest != "FFFF":
            sendAndWaitForOk("AT+DEST=FFFF\r\n")
            currDest = "FFFF"
        sendAndWaitForOk("AT+SEND=3\r\n")
        ser.write("RTI\r\n")
        time.sleep(randint(30, 60))
        
def sendMessage(addr, m):
    global currDest
    global knownAddr
    if addr not in knownAddr:
        print("Address not discovered " + addr)
        return
    if currDest != addr:
        sendAndWaitForOk("AT+DEST=" + addr + "\r\n")
        currDest = addr
    print("12")
    sendAndWaitForOk("AT+SEND=" + str(len(m)) + "\r\n")
    print("13")
    ser.write(m)
    print("message sent")
            

start_new_thread(receive, ())
start_new_thread(processReceived, ())
start_new_thread(sendRti, ())

while 1:
    input = raw_input()
    if input == 'exit':
        break
    elif input == "printtable":
        print(knownAddr)
    elif input.startswith("send"):
        parts = input.split(";")
        if len(parts) != 3:
            print("wrong format")
        else:
            sendMessage(parts[1], parts[2])
    else:
        ser.write(input + '\r\n')
    
ser.close()