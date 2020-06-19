import socket
import json
from os import system

import client.config as cfg
from packets.packets import makeClientDataDict

class serverHistory:
    def __init__(self):
        try:
            file = open(cfg.serversJsonPath, 'r')
            self.dict = json.load(file)

        except:
            file = open(cfg.serversJsonPath, 'w')
            self.dict = {}
        file.close()

    def add(self,ip,name):
        self.dict[ip] = name

        file = open(cfg.serversJsonPath, 'w')
        json.dump(self.dict,file)
    

    def getOnline(self):
        ips = [ip for ip in self.dict.keys()]
        names = [self.dict[ip] for ip in ips]
        isOnline = []
        for ip in self.dict.keys():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            if s.connect_ex((ip,cfg.port)) == 0:
                
                isOnline.append(True)
            else:
                isOnline.append(False)
            s.close()
        return ips,names,isOnline




def getSaved(gui):
    try:
        file = open(cfg.userJsonPath, 'r')
        userDict = json.load(file)

    except:
        file = open(cfg.userJsonPath, 'w')
        username = gui.prompt("Whats Your Name?",endChar="")
        gui.addText(f"Hi {username}!",cfg.subTextColor)

        for i,color in enumerate(cfg.clientColors):
            gui.addText(f"{i}: {color}",color,endChar="")
        gui.addText("",endChar="")

        #loops until valid input
        while True:
            inStr = gui.prompt("Whats Your Color (Number)?",endChar="").strip()
            try:
                color = cfg.clientColors[int(inStr)]
                break
            except:
                gui.addText(f"{inStr} Isnt an Option",cfg.subTextColor)
                continue
        
        gui.addText(f"{color} Chosen",cfg.subTextColor)

        userDict = makeClientDataDict(0,username,color)
        json.dump(userDict,file)

    return userDict

#used to get ip from user input (allows user to type room name instead of ip)
def getIpFromStr(serversDict,inStr):
    inStr.strip()
    inStr = inStr.lower()

    if inStr=="localhost":
        return "127.0.0.1"

    for ip in serversDict.keys():
        if inStr == serversDict[ip].lower():
            return ip

    return inStr
    





#-------------------#
#  Socket Wrappers  #
#-------------------#
def startSocket(ip):
    #ipv4 socket using tcp
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #connect to server
    sock.settimeout(cfg.connTimeOut)
    sock.connect((ip, cfg.port))
    sock.settimeout(cfg.waitTime)
    return sock