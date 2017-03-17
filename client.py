#!/usr/bin/env python3
from yarong import *

class YarongClient(YarongNode):

    """docstring for ."""
    def __init__(self, host='', host_ip='localhost', host_port=8888, listener_timeout_in_sec=2):
        super(YarongClient, self).__init__(host, host_ip, host_port, listener_timeout_in_sec)

        self.listener_socket = None
        self.input_socket = None
        self.init_socket_connect()

    def init_socket_connect(self):
        self.listener_socket = self.create_socket()
        self.input_socket = self.create_socket()

        self.listener_socket.connect((self.host_ip , self.host_port))
        self.input_socket.connect((self.host_ip , self.host_port))


    def is_close(self,data):
        return data == CLOSE_MSG

    def close(self):
        import time
        self.threads_stop_event.set()
        print("Closing....")
        time.sleep(self.close_delay_in_sec)

        self.input_socket.close()
        self.listener_socket.close()
        print("All sockets closed")

    def quit(self):
        self.input_socket.sendall(QUIT_MSG.encode())
        self.threads_stop_event.set()
        self.close()


    def welcome(self):
        with open('welcome_msg') as f:
            print(f.read())


    def run(self):
        listener_thread_kwargs = {
        "socket":self.listener_socket, "event": self.threads_stop_event,
        "client": self, "other_client_port": self.host_port
        }
        listener_thread = YarongClientListenerThread(kwargs=listener_thread_kwargs)
        listener_thread.start()

        input_thread_kwargs = {
        "socket":self.input_socket, "event": self.threads_stop_event,
        "client": self
        }
        input_thread = YarongClientInputThread(kwargs=input_thread_kwargs)
        input_thread.start()

        try:
            print("waiting for event to be set")
            self.threads_stop_event.wait()
            print("event was set")

        except KeyboardInterrupt:
            self.quit()
        finally:
            print("Over")



class YarongClientListenerThread(threading.Thread):
    """docstring for ."""
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         daemon=daemon)
        self.socket = kwargs["socket"]
        self.threads_stop_event = kwargs["event"]
        self.client = kwargs["client"]
        self.other_client_port = kwargs["other_client_port"]

    def is_session_close(self, data):
        return data == CLOSE_MSG

    def prompt_message(self, encoded_msg):
        logging.debug(encoded_msg.decode())

    def run(self):
        #Sending message to client_connected client
        self.socket.sendall('Welcome to the server. Type something and hit enter\n'.encode())

        #infinite loop so that function do not terminate and thread do not end.
        while not self.threads_stop_event.is_set():
            ready = select.select([self.socket], [], [], self.client.listner_socket_timeout_in_sec)

            if self.threads_stop_event.is_set():
                '''
                Case: When a user sends "/quit".
                The client will close itself. However this loop might be not
                synchronized so it will call self.client.close() again.
                Thus "return".
                '''
                return

            #Receiving from client

            if not ready[0]:
                continue

            data = self.socket.recv(1024)

            if not data or self.is_session_close(data.decode()):
                print("Session closes")
                break

            self.prompt_message(data)

        #came out of loop
        self.client.close()



class YarongClientInputThread(threading.Thread):
    """docstring for ."""
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         daemon=daemon)
        self.socket = kwargs["socket"]
        self.threads_stop_event = kwargs["event"]
        self.client = kwargs["client"]

    def is_quitting(self, msg):
        return msg == QUIT_MSG

    def run(self):
        while not self.threads_stop_event.is_set():

            # Non-blocking user input mechanism
            # Read "Keyboard input with timeout in Python":
            # http://stackoverflow.com/a/2904057/3067013
            user_input_sources, _, _ = select.select(
                [sys.stdin],    # Reads
                [],             # Writes
                [],             # Exceptions
                self.client.listner_socket_timeout_in_sec
            )
            if not user_input_sources:
                continue

            message = user_input_sources[0].readline().strip()

            if self.is_quitting(message):
                self.client.quit()
                break

            try :
                #Set the whole string
                self.socket.sendall(message.encode())
            except socket.error:
                #Send failed
                print('Send failed')
                self.client.close()

        print("leave input_thingie")


if __name__ == "__main__":
    yarongClient = YarongClient()
    yarongClient.run()
