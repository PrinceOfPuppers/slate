import socket
from time import sleep
import marshal
import csv
import re
from urllib.request import urlopen
import server.config as cfg

def saveRoomName(name):
    file = open(cfg.roomNamePath, 'w')
    file.write(name)
    file.close()
    

def getRoomName():
    try:
        file = open(cfg.roomNamePath, 'r')
        name = file.readline()
        
        
        if not name:
            file = open(cfg.roomNamePath, 'w')
            name = input("What Would You Like To Name This Chat Room: ")
            file.write(name)

        file.close()

    except IOError:
        name = input("What Would You Like To Name This Chat Room: ")
        saveRoomName(name)
    
    print(f"Server Name: {name}")
    return name
    


#if 2 users have the same username, one joining is given a suffix
def ensureUniqueUsername(username,roomName,clients):
    #prevent no name
    if username == "":
        username = cfg.noNameReplacement

    #prevent server name
    elif username == roomName:
        suffix = 1

    #prevent duplicate name
    else:
        suffix=""
    i=0
    while i < len(clients):
        clientName = clients[i].dict["username"]
        if username+str(suffix) == clientName:
            if suffix=="":
                suffix=1
            else:
                suffix+=1

            i=0
        else:
            i+=1

    return username+str(suffix)

#-------------------#
#  Socket Wrappers  #
#-------------------#
def startServer():
    #waits for server to close before restarting
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            externalIp = urlopen('https://api.ipify.org').read().decode('utf8')
            internalIp = socket.gethostbyname(socket.gethostname())

            s.bind(("", cfg.port))
            print(f"Server Started with external IP: {externalIp}, internal IP {internalIp}, and port: {cfg.port}\n")
            s.listen(cfg.queueLen)
            return s,externalIp,internalIp
        except:
            sleep(1)


#returns list of inputs 
def sanitizeInput(inputStr):
    inputStr.strip()

    #removes multiple spaces
    inputStr = re.sub(" +", " ",inputStr)

    inputList = [ str(x) for x in list(csv.reader([inputStr], delimiter=' ', quotechar='"'))[0] ]

    for i,val in enumerate(inputList):
        inputList[i]=val.replace('"',"")
        inputList[i]=val.replace("'","")

    return inputList