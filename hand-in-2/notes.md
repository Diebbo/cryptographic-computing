# Hand in 2, Implementation details

Implement a secure two-party protocol for the blood type compatibility function
using the one-time truth table protocol. Since the goal of the exercise is to
better understand the protocol (not to build a full functioning system), feel
free to implement all parties on the same machine and without using network
communication.

# Entities

- client.py: taking as input the player number (1,0) and the address the server is.
- server.py: handle the communication betwenn the two.

# Initialization

Server starts given the truth table matrix.

# Endpoints

On connecting to `/compute/{playerId}`

1. It generates r and s in {0,1}^n
2. Choose a matrix M_0 at random and then computes M\_1 as the xor between real
   (shifterd by r on rows and s on columns) and masking one.
3. Gives M0, r to the first one and M1, s to the second

`/forward/{round}/{playerId}`: the servers saves what should be forwarded in a local
state.

`/get/{round}/{playerId}` each player extracts the information from his inbox.

# Player game
