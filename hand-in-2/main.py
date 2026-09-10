import random

"""
Implementing one time truth table for blood type compatibility:
    A : b1 b2 b3
    B : b1 b2 b3
    OUTPUT: A or (not B)
"""


class Dealer:
    def __init__(self):
        self.can_receive_table = [
            [1, 0, 0, 0, 0, 0, 0, 0],  # O-
            [1, 1, 0, 0, 0, 0, 0, 0],  # O+
            [1, 0, 1, 0, 0, 0, 0, 0],  # A-
            [1, 1, 1, 1, 0, 0, 0, 0],  # A+
            [1, 0, 0, 0, 1, 0, 0, 0],  # B-
            [1, 1, 0, 0, 1, 1, 0, 0],  # B+
            [1, 0, 1, 0, 1, 0, 1, 0],  # AB-
            [1, 1, 1, 1, 1, 1, 1, 1],  # AB+
        ]
        # random shift of columns and rows
        self.s, self.r = (random.randint(0, 7), random.randint(0, 7))
        self.randomMatrix = [[random.randint(0, 1) for _ in range(8)] for _ in range(8)]

    def RandA(self):
        # give shifted matrix A
        matA = [
            [
                (
                    self.can_receive_table[(i - self.r) % 8][(j - self.s) % 8]
                    ^ self.randomMatrix[i][j]
                )
                for j in range(8)
            ]
            for i in range(8)
        ]

        # shift rows by r and s
        return (matA, self.r)

    def RandB(self):
        return (self.randomMatrix, self.s)


class Bob:
    def __init__(self):
        self.y = None
        self.u = None

    def Init(self, y, rand_b):
        self.y = y
        matB, s = rand_b
        self.s = s
        self.matB = matB

    def Send(self):
        # send v, matB[u][v=y+s]  // u = r + x
        self.v = (self.y + self.s) % 8
        return (self.v, self.matB[self.u][self.v])

    def Receive(self, value):
        self.u = value


class Alice:
    def __init__(self):
        self.x = None
        self.u = None
        self.v = None
        self.zb = None

    def Init(self, x, randA):
        matA, r = randA
        self.x = x
        self.r = r
        self.matA = matA

    def Send(self):
        self.u = (self.r + self.x) % 8
        return self.u

    def Receive(self, value):
        self.v = value[0]
        self.zb = value[1]

    def Output(self):
        return self.zb ^ self.matA[self.u][self.v]


def convert(blood_type):
    blood_type_map = {
        "O-": 0,
        "O+": 1,
        "A-": 2,
        "A+": 3,
        "B-": 4,
        "B+": 5,
        "AB-": 6,
        "AB+": 7,
    }
    return blood_type_map[blood_type]


if __name__ == "__main__":
    # x, y = input("Enter two blood types separated by space (e.g., A+ B-):").split()
    x, y = "A+", "O-"
    # convert blood type to index
    x = convert(x)
    y = convert(y)
    Dealer = Dealer()
    Alice = Alice()
    Bob = Bob()
    Alice.Init(x, Dealer.RandA())
    Bob.Init(y, Dealer.RandB())
    Bob.Receive(Alice.Send())
    Alice.Receive(Bob.Send())
    z = Alice.Output()
    ostring = "compatible, i.e. B can donate to A" if z == 1 else "not compatible"
    print(f"The two blood types are {ostring}")
