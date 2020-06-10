import threading
from queue import Queue

#holds client data and thread locks
class ClientData:
    def __init__(self,sock,address,username,Id):
        self.lock=threading.Lock()

        self.lock.acquire()
        self.username = username
        self.id = Id
        self.sock=sock
        self.lock.release()

    def remove(self,clientList):
        self.lock.acquire()
        clientList.remove(self)
        self.sock.close()
        self.lock.release()
        return self.username
    

class MessageQueue:
    def __init__(self):
        self.queue=Queue()
    def put(self,message, username="", messangerID = -1):
        self.queue.put((username,message,messangerID))
    def get(self):
        val = self.queue.get()
        return val[0],val[1],val[2]
    def empty(self):
        return self.queue.empty()