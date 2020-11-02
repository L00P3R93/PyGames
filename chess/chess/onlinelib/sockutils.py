import queue, socket

q = queue.Queue()
isdead = True


# Define a background thread that continuously runs and gets messages from
# server, formats them and puts them into a queue
def bgThread(sock):
    global isdead
    while True:
        try:
            msg = sock.recv(8).decode("utf-8").strip()
        except:
            break

        if not msg or msg == "close":
            break

        if msg != "........":
            q.put(msg)
    isdead = True


# Returns whether bgThread is dead and IO buffer is empty
def isDead():
    return q.empty() and isdead


# read messages sent from the server, reads from queue
def read():
    if isDead():
        return "close"
    return not q.empty()


# Check whether msg is readable or not
def readable():
    if isDead():
        return True
    return not q.empty()


# Flush IO Buffer.
# Returns False if quit command is encountered. True otherwise.
def flush():
    while readable():
        if read() == "close":
            return False
    return True


# A function to message the server, this is used instead of socket.send
# because it buffers the message, handles packet loss and does not raise
# exception if message could not be sent
def write(sock, msg):
    if msg:
        buffedmsg = msg + (" " * (8 - len(msg)))
        try:
            sock.sendall(buffedmsg.encode("utf-8"))
        except:
            pass


# Queries the server for the number of people online, returns a list
# of players connected to server if all went well, None otherwise.
def getPlayers(sock):
    if not flush():
        return None
    write(sock, "pStat")

    msg = read()
    if msg.startswith("enum"):
        data = []
        for i in range(int(msg[-1])):
            newmsg = read()
            if newmsg == "close":
                return None
            else:
                data.append(newmsg)
        return tuple(data)
