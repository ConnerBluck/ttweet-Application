import argparse
import errno
import json
import select
import socket
import sys
import threading
import time

thread_count = 0
clients = {}

# List to hold error messages. This exists to make things easier on the eyes
response_messages = [
    "username already taken",
    "no message received",
    "no response",
    "exiting"
]

# Object class to hold a definition of each user and their specific information
class User:
    def __init__(self, username):
        self.username = username
        self.tweets = [] # This should hold a list of tuples of the form (tweet message, tweet hashtags)
        self.timeline_tweets = []
        self.hashtags = set()
        self.thread = None

# Function to handle the messages sent by the client
# Returns
#   False if the client exited
#   None if nothing was received
#   Static string for specialized server response (if any message is to be sent back to server)
#   User tuple if the inputted information was valid for new client connection
#   Other built string based on client's requested command
def receive_message(client_socket):
    recv_message = None
    # Attempt to receive response from server, catching any faults if they occur
    try:
        recv_message = client_socket.recv(1024).decode('unicode_escape')

        if (not len(recv_message)):
            return None

        message = json.loads(recv_message)

        if (message["command"] == "create"):
            # Checks if new client's chosen username has already been taken
            for socket in clients:
                if message["username"] == clients[socket].username:
                    return response_messages[0]

            return User(message["username"])
        elif message["command"] == "tweet":
            # Adds a new tweet to the client's tweet history
            clients[client_socket].tweets.append((message["message"], message["hashtags"]))

            tags = message["hashtags"].split('#')
            tags = tags[1:]
            for x in clients:
                for y in clients[x].hashtags:
                    if y in tags or y == "ALL":
                        clients[x].timeline_tweets.append((message["username"], message["message"], message["hashtags"]))  
                        break  

            # Return "no response" to indiciate that the server does not need to send anything back
            return response_messages[2]
        #code to handle getusers command and put all users into a string to send to client
        elif message["command"] == "getusers":
            client_list = ""
            for socket in clients:
                client_list = client_list + clients[socket].username + "\n"
            client_list = client_list[:-1]
            return client_list

        elif message["command"] == "subscribe":
            cur_hashtags = clients[client_socket].hashtags
            hashtag = message["hashtag"]

            if hashtag[1:] in cur_hashtags or len(cur_hashtags) == 3:
                return "operation failed: sub " + hashtag + " failed, already exists or exceeds 3 limitation"
            cur_hashtags.add(hashtag[1:])
            return "operation success"

        #unsubscribes the client from a hashtag, handles unsubscribing from all hashtags, and handles the cases where the hashtag was never subscribed to 
        elif message["command"] == "unsubscribe":
            curr_hashtags = clients[client_socket].hashtags
            hashtag = message["hashtag"]
            if hashtag[1:] == "ALL":
                curr_hashtags.clear()
                return "operation success"
            if len(curr_hashtags) == 0:
                return "Hashtag not found"
            if hashtag[1:] not in curr_hashtags:
                return "Hashtag not found"
            curr_hashtags.remove(hashtag[1:])
            return "operation success"

        #code to handle gettweets command and put all tweets of specified user into a string to send to client
        elif message["command"] == "gettweets":
            user_tweets = ''
            for i in clients:
                if clients[i].username == message["username"]:
                    if len(clients[i].tweets) == 0:
                        #if client had no tweets, return this message
                        return message["username"] + " has no tweets in the system"
                    for j in clients[i].tweets:
                        #put all of clients tweets in correct format
                        user_tweets = user_tweets + message["username"] + ': \"' + j[0] + '\" ' + j[1] + '\n'
                    user_tweets = user_tweets[:-1]
                    return user_tweets
            #if client doesn't exist, return this message
            return "no user " +  message["username"] + " in the system"
        #code to handle timeline command and put all timeline_tweets into a string and send to client
        elif message["command"] == "timeline":
            timeline_tweets = ''

            if (len(clients[client_socket].timeline_tweets) == 0):
                return "no tweets in timeline"

            for i in clients[client_socket].timeline_tweets:
                timeline_tweets = timeline_tweets + i[0] + ': \"' + i[1] + '\" ' + i[2] + '\n'
            timeline_tweets = timeline_tweets[:-1]

            return timeline_tweets

        #Handles the exit command, returns None which closes the client when returned as a message
        elif message["command"] == "exit":
            return False

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            # Return "no message received" to indicate that there was nothing sent from the client held in the buffer
            return response_messages[1]

# Function to handle a new thread's (client's) connection to the server, infinitely polling for sent messages
def threaded_main(client_socket):
    try:
        while True:
            message = receive_message(client_socket)

            # Check if server should send back a response to the client
            if (message != response_messages[1] and message != response_messages[2]):
                # Delete user from server memory if they have chosen to exit their connection
                if (message == False):
                    del clients[client_socket]
 
                    global thread_count
                    thread_count -= 1
                    
                    break

                elif (message == None):
                    continue

                # Send back response to client
                message = message.encode()
                client_socket.send(message)
    except KeyboardInterrupt as e:
        quit()

if __name__ == "__main__":
    # Parser to parse the command line input that starts the server
    parser = argparse.ArgumentParser()
    parser.add_argument(type=int, dest='server_port')

    try:
        # Check if too few arguments were passed in
        if (len(sys.argv) < 2):
            raise Exception

        args = parser.parse_args()
    except Exception:
        print("error: args should contain <ServerPort>")
        quit()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", args.server_port)) # 0.0.0.0 allows for any IP address given by the client to be acceptable
    server_socket.listen(5)

    print("Server socket is listening...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()

            if (thread_count < 5):
                # Receive and handle the message sent by the new client
                new_user = receive_message(client_socket)

                # Send acceptance/refusal message of new client connection if the client's username does not already exist
                if (isinstance(new_user, User)):
                    clients[client_socket] = new_user

                    send_message = "username legal, connection established."
                    client_socket.send(send_message.encode())

                    thread_count += 1

                    # Enter function to handle new thread's client and interactions with the server
                    threading.Thread(target=threaded_main, args=(client_socket, )).start()
                else:       
                    send_message = "username illegal, connection refused."       
                    client_socket.send(send_message.encode())
                    client_socket.close()
            else:
                send_message = "error: max users logged in, connection refused."       
                client_socket.send(send_message.encode())
                client_socket.close()
    except ConnectionResetError as e:
        pass # Has to do with server overload, keeps connection alive
    except Exception as e:
        # Cleanup server if server disconnects
        for socket in clients:
            socket.close()
        
        server_socket.close()
        print("Server has closed")
        quit()