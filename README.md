# ttweet-Application

## **1. Implementation Ideas**

The server creates socket and listens.
The client connects if username is not already taken and there are less than 5 clients connected.
A command from the client is checked for input errors in the client, then the necessary parts of the command line are sent to the server.
The server reads these commands and sends back the necessary information.
The client prints out the necessary response message.
Requests sent to the server are in the form of a json string to make parsing necessary information easier.
Every json request will have a 'command' to indicate what the user would like to do:

    create (new user, the user themselves will not type this command)
    tweet
    subscribe/unsubscribe
    gettweets
    timeline
    getusers
    exit

In addition to the command, several other subjects will be included in the string as well. For example, many commands have 'user' and subscribe/unsubscribe have 'hashtag'.
The server will then examine the 'command' upon receiving the client's message and determine an appropriate response. The server may send back a static message, a specialized one based on exisiting data within the server, and other times it will send back nothing at all if the client's request required no feedback.

**Functions in ttweetsrv.py**

    main -> main function entered upon starting the server file, will mainly listen for and accept client connections when it has available client slots
    threaded_main -> entered from main upon a new client being connected to the server as well as its dedicated thread, will continuously listen for requests sent from the dedicated client
    receive_message -> entered from threaded_main to listen for and handle messages sent by the client

**Objects in ttweetsrv.py**

    User -> holds information specific to this client including their username, running thread, tweet history (including hashtags), subscriptions, and timeline 

**Functions in ttweetcl.py**

    main -> main function entered upon starting the client file, will continuously accept user input and build request json strings to send to server
    handle_subscribe -> handles the 'subscribe' input given by the user when the command is requested, including any errors in formatting
    handle_unsubscribe -> handles the 'unsubscribe' input given by the user when the command is requested, including any errors in formatting
    handle_tweet -> handles the 'tweet' input given by the user when the command is requested, including any errors in formatting
    connected_exit -> will release any resources the client's socket is connected to before closing it
    handle_exit -> handles the 'exit' input given by the user when the command is requested, including any errors in formatting
    send_json -> builds the dictionary of necessary request information, turns it into a string, and sends it to the server

**client/server connection:**

    multithreading: a new thread is creating for each new client connection
    tweet: each tweet is stored as a pair of (message, hashtags) and added to the user's tweet history
    subscribe: each subscription is added to a user's list of subscriptions
    unsubscribe: will remove the desired subscriptions from a user's list of subscriptions
    timeline: each tweet made by any user connected to the server that has any of this user's subscribed tags will be added to this user's timeline list of tweets
    getusers: will return all users currently connected to the client by visiting a dedicated structure of client connections
    gettweets: will return all tweets made by an indicated user by returning their tweet history
    exit: will remove the client's connection to the server and open up a slot for a new client connection

## **2. Responsibilities**

Tahlee Jaynes: Responsible for implementing the tweet command, setting up the client/server connection, and multithreading.  

Conner Bluck: Responsible for implementing the getusers, gettweets, and timeline commands.

Katie Jordan: Responsible for implementing the subscribe and unsubscribe commands along with exit.

## **3. How to use**
    1- Open one terminal and login to a GT Shuttle
        1- Enter 'ssh cc-shuttle1.cc.gatech.edu -l [gburdell]'
        2- Enter your GT password
    2- Open the server
        1- Enter 'python3 ttweetsrv.py [valid port number]'
    3- Open another terminal and repeat the process to login to a GT Shuttle
    4- Open a client (can open up to 5 clients, 5 different terminals, each client must have a different username)
        1- Enter 'python3 ttweetcl.py [valid IP address] [valid port number] [username]'
    5-Use the different commands to use the app
        tweet “<150 char max tweet>” <Hashtag>: 
        subscribe <Hashtag>: subscribes the client to a Hashtag
        unsubscribe <Hashtag>: unsubscribes the client from a Hashtag
        timeline: outputs the tweets sent to the client by the server line-by-line
        getusers: gets all of the users that are logged on
        gettweets <Username>: gets all of the tweets sent by a user
        exit: logs the user out, deleting the account

## **4. How to install dependent packages/ any special instructions for being able to test your code**
    No external packages necessary to run this client/server
## **5. Limitations**
    Right now the server has a difficult time releasing its resources upon a requested disconnect (it can release successfully upon encountering an error).
    The server may also have a difficult time sending and the client a difficult time in receiving particularly large data withtout it being lost such as those continuously stored within a user's timeline.
    Although by design, the server can only handle a maximum of 5 concurrent client connections.

