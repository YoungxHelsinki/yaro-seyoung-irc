import socket
import sys
from thread import *

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

'''
connections = {0: (speaker, listener)}
'''
connections = {}
connections_client_listening = [] # Store all connectioins.
connections_client_speaker = [] # Store all connectioins.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'

#Start listening on socket
s.listen(10)
print 'Socket now listening'

def is_client_quitting(msg):
    return msg == "/quit"

def propagate_msg(msg, sender=None):
    if sender:
        for c in connections.keys():
            if c is not sender:
                connections[c][0].sendall(msg)
    else:
        for c in connections.keys():
            connections[c][0].sendall(msg)



#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #Sending message to connected client
    conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
    client_port = connections[conn][1][1]

    #infinite loop so that function do not terminate and thread do not end.
    while True:

        #Receiving from client
        data = conn.recv(1024)

        if is_client_quitting(data):
            break

        msg = '[%s]>>> %s' % (client_port, data)
        if not data:
            break

        propagate_msg(msg, conn)
        # conn.sendall(reply)

    #came out of loop
    connections[conn][0].close()
    conn.close()
    connections.pop(conn, None)

    msg = "Client %s left the channel." % (client_port)
    propagate_msg(msg)
    print(msg)

#now keep speaker with the client
while 1:
    #wait to accept a connection - blocking call
    conn_listener, addr_listener = s.accept()
    conn_speaker, addr_speaker = s.accept()
    print 'Connected with ' + addr_listener[0] + ':' + str(addr_listener[1])
    connections[conn_speaker] = (conn_listener, addr_speaker)
    
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread ,(conn_speaker,))

s.close()
