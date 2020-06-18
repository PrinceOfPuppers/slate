import threading

def startThreads(client):
    jobs = client.threadJobs

    retrieveTread = threading.Thread(target = client.recievingLoop)
    retrieveTread.daemon = True
    retrieveTread.start()
    client.threads[jobs[0]] = retrieveTread

    transmitTread = threading.Thread(target = client.transmit)
    transmitTread.daemon = True
    transmitTread.start()
    client.threads[jobs[1]] = transmitTread


def nonDaemon(target,args):
    t = threading.Thread(target=target,args=args)
    t.start()