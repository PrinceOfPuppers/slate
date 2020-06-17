import threading
import json

from packets.packets import makeClientDataDict,PType


#holds client data and thread locks
class ClientData:
    def __init__(self,sock,ip,clientDict):
        self.lock=threading.Lock()

        self.lock.acquire()
        self.sock=sock

        self.ip = ip
        self.dict = clientDict
        self.lock.release()

    def __str__(self):
        username = self.dict["username"]
        clientID = self.dict["id"]
        color = self.dict["color"]
        clientInfo = f"username: {username}, id: {clientID}, ip: {self.ip}, color: {color}"
        return clientInfo
        
    def remove(self,clientList):
        self.lock.acquire()
        clientList.remove(self)
        self.sock.close()
        self.lock.release()
    
    def packageData(self):
        return self.dict
    

        


