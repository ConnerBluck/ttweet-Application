import argparse
import errno
import json # JSON library is used to cleanly hold info sent between client/server
import os
import re
import socket
import sys
import time

# Function to handle the subscribe command
# command_string -> the command + the hashtag
#   subscribe command looks like > subscribe <hashtag>
# Return
#   False if there was an error in the input format
#   hashtag to send inside message to server
def handle_subscribe(input_command):
    msg_split = input_command.split(' ')
    if len(msg_split) != 2:
        print("message format illegal.")
        return False
    hashtag = msg_split[1]
    if len(hashtag) < 2 or hashtag[0] != '#' or not hashtag[1:].isalnum():
        print("hashtag illegal format, connection refused.")
        return False
    return hashtag

# Function to handle the unsubscribe command
# command_string -> the command + the hashtag
#   unsubscribe command looks like > unsubscribe <hashtag>
# Return
#   False if there was an error in the input format
#   hashtag to send inside message to server
def handle_unsubscribe(input_command):
    msg_split = input_command.split(' ')
    if len(msg_split) != 2:
        return False
    hashtag = msg_split[1]
    if len(hashtag) < 2 or hashtag[0] != '#':
        return False
    return hashtag

# Function to handle the tweet command
# command_string -> string after "tweet" in the user's input
#   tweet command looks like > tweet <"message"> <hashtag>
# Return
#   False if there was an error in the input format
#   tuple of [tweet message, tweet hashtags] to send inside message to server
def handle_tweet(command_string):
    tweet_input = command_string[1].split('"', 2)
    message = tweet_input[1]
    hashtag_string = tweet_input[2].strip()

    if (len(tweet_input) != 3 or len(message) == 0):
        print("message format illegal.")
        return False
    elif (len(message) > 150):
        print("message length illegal, connection refused.")
        return False
    elif (re.search(" ", hashtag_string) != None or re.search("##", hashtag_string) != None or len(re.split("#", hashtag_string)) > 5):
        print("hashtag illegal format, connection refused.")
        return False
    else:
        hashtags = re.split("#", hashtag_string)

        # Variable to ignore the first index of the split array which is the space before the first #
        count = 0

        for tag in hashtags:
            if (count > 0 and (len(tag) == 0 or tag == 'ALL')):
                print("hashtag illegal format, connection refused.")
                return False
            
            count += 1

    return [message, hashtag_string]

# Function to handle the exit command
# command_string -> the command
#   exit command looks like > exit
# Return
#   False if there was an error in the input format, anything other than exit
#   the message
def handle_exit(input_command):
    msg_split = input_command.split(' ')
    if len(msg_split) != 1:
        print("message format illegal.")
        return False
    return msg_split

# Create JSON object to hold the command and supplementary information then send to server
def send_json(dict, client_socket):
    client_message = json.dumps(dict)
    client_message = client_message.encode('unicode_escape')
    client_socket.send(client_message)

# Handles exiting if the client socket is connected to the server, releasing its resources before exiting this process
def connected_exit(socket):
    socket.close()
    quit()

if __name__ == '__main__':
    # Parser to parse the command line input that starts the client
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='server_ip')
    parser.add_argument(dest='server_port')
    parser.add_argument(dest='username')

    try:
        # Check if too few arguments were passed in
        if (len(sys.argv) < 4):
            # Throw dummy Exception to catch for customized error message
            raise Exception
        args = parser.parse_args()
    except Exception:
        print("error: args should contain <ServerIP> <ServerPort> <Username>")
        quit()

    # Regex string to validate IPv4 format of inputted IP address
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
 
    if (not re.search(regex, args.server_ip)):
        print("error: server ip invalid, connection refused.")
        quit()

    # Validate that inputted port number is actually an integer
    try:
        args.server_port = int(args.server_port)
    except Exception:
        print("error: server port invalid, connection refused.")
        quit()

    # Regex string to validate that inputted username is alphanumeric
    regex = "^[A-Za-z0-9]*$"

    if (not bool(re.match(regex, args.username)) or args.username == "" or args.username == " " or len(args.username) > 15):
        print("error: username has wrong format, connection refused.")
        quit()

    # Attempt to set up connection between new client socket and server
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.server_ip, args.server_port))
        client_socket.setblocking(True)
    except ConnectionRefusedError:
        # Server is not booted up
        print("connection error, please check your server: Connection refused")
        quit()
    except Exception:
        # Other error in connecting to server
        print("error setting up connection to server")
        quit()

    # Create JSON object to hold info to first send to server. 
    # This first message will only hold the necessary command to execute 
    #   (user creation) and the supplementary information to execute it (username inputted) 
    user_message = json.dumps({"command": "create", "username": args.username})
    user_message = user_message.encode('unicode_escape') # unicode_escape allows for easier conversion from JSON dict to string
    client_socket.send(user_message)
    server_message = None

    # Attempt to receive response from server, catching any faults if they occur
    try:
        server_message = client_socket.recv(1024).decode()

        print(server_message)

        if (server_message == "username illegal, connection refused."):
            connected_exit(client_socket)
        if (server_message == "error: max users logged in, connection refused."):
            connected_exit(client_socket)
    except OSError:
        print("error: max users logged in, connection refused.")
        connected_exit(client_socket)
    except Exception:
        None

    while True:
        try:
            input_command = None
            
            # Keep client connection persistent by infinitely waiting for the user's input
            try:
                input_command = input()
            except:
                connected_exit(client_socket)

            # The only info in front of the first space should be the command to execute (tweet, subscribe, etc.)
            command_string = input_command.split(' ', 1)

            client_message = None

            # Check which command the user wants to execute, checking for proper formatting and deciding whether to wait for a server response if need be
            if (command_string[0] == 'tweet') :
                result = handle_tweet(command_string)
                
                if (not isinstance(result, bool)):
                    send_json({"command": "tweet", "username": args.username, "message": result[0], "hashtags": result[1]}, client_socket)
                    
                continue
            elif (command_string[0] == "getusers"):

                if (len(command_string) == 1):
                    send_json({"command": "getusers"}, client_socket)
                else:
                    print("message format illegal.")
                    continue
            elif (command_string[0] == "subscribe"):
                result = handle_subscribe(input_command)

                if (not isinstance(result, bool)):
                    send_json({"command": "subscribe", "hashtag": result}, client_socket)
                else:
                    continue
            elif (command_string[0] == "unsubscribe"):
                result = handle_unsubscribe(input_command)

                if (not isinstance(result, bool)):
                    send_json({"command": "unsubscribe", "hashtag": result}, client_socket)
                else:
                    continue
            elif (command_string[0] == "exit"):
                result = handle_exit(input_command)
                if (not isinstance(result, bool)):
                    send_json({"command": "exit"}, client_socket)
                    print("bye bye")
                    connected_exit(client_socket)
                else:
                    print("message format illegal.")
                    continue
            elif (command_string[0] == "gettweets"):
                if (len(command_string) == 2):
                    send_json({"command": "gettweets", "username": command_string[1]}, client_socket)
                else:
                    print("message format illegal.")
                    continue
            elif (command_string[0] == "timeline"):
                if (len(command_string) == 1):
                    send_json({"command": "timeline"}, client_socket)
                else:
                    print("message format illegal.")
                    continue
            else:
                print("message format illegal.")
                continue

            # Attempt to receive response from server, catching any faults if they occur
            try:
                server_message = client_socket.recv(16384).decode()
                
                if server_message != 'operation failed':
                    print(server_message)
            except IOError as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    continue

        except KeyboardInterrupt:
            connected_exit(client_socket)