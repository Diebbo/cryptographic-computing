# Hand in 2, Implementation details

```
can_receive_table = [
#0- 0+ A- A+ B- B+AB-AB+
[1, 0, 0, 0, 0, 0, 0, 0], # O-
[1, 1, 0, 0, 0, 0, 0, 0], # O+
[1, 0, 1, 0, 0, 0, 0, 0], # A-
[1, 1, 1, 1, 0, 0, 0, 0], # A+
[1, 0, 0, 0, 1, 0, 0, 0], # B-
[1, 1, 0, 0, 1, 1, 0, 0], # B+
[1, 0, 1, 0, 1, 0, 1, 0], # AB-
[1, 1, 1, 1, 1, 1, 1, 1], # AB+
]
```

Implement a secure two-party protocol for the blood type compatibility function
using the one-time truth table protocol. Since the goal of the exercise is to
better understand the protocol (not to build a full functioning system), feel
free to implement all parties on the same machine and without using network
communication.

We're handlying the assignment by using some classes in python.

# Entities

- Dealer class taking as input the player number (1,0) and the address the server is.
- Player handle the communication betwenn the two.

# Initialization

Dealer starts given the truth table matrix.

# Classes

Dealer
`genPramas(M) -> ((int, Mat), (int, Mat))`

1. It generates r and s in {0,1}^n
2. Choose a matrix M_0 at random and then computes M\_1 as the xor between real
   (shifterd by r on rows and s on columns) and masking one.
3. Gives M0, r to the first one and M1, s to the second

Player
`computePublicParam((int, Mat)) -> int`
`computeMatrix(Mat, Mat) -> Mat`
