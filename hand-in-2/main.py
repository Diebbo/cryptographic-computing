import random
import sys

"""
Implementing one time truth table for blood type compatibility:
    A : b1 b2 b3
    B : b1 b2 b3
    OUTPUT: A or (not B)
"""

# Blood types in the order used by the rows/columns of the truth table.
BLOOD_TYPES = {
    "O-": 0,
    "O+": 1,
    "A-": 2,
    "A+": 3,
    "B-": 4,
    "B+": 5,
    "AB-": 6,
    "AB+": 7,
}


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
    def __init__(self, y, rand_b):
        self.y = y
        matB, s = rand_b
        self.s = s
        self.matB = matB
        self.u = None

    def Send(self):
        # send v, matB[u][v=y+s]  // u = r + x
        self.v = (self.y + self.s) % 8
        return (self.v, self.matB[self.u][self.v])

    def Receive(self, value):
        self.u = value


class Alice:
    def __init__(self, x, randA):
        self.x = x
        matA, r = randA
        self.r = r
        self.matA = matA
        self.u = None
        self.v = None
        self.zb = None

    def Send(self):
        self.u = (self.r + self.x) % 8
        return self.u

    def Receive(self, value):
        self.v = value[0]
        self.zb = value[1]

    def Output(self):
        return self.zb ^ self.matA[self.u][self.v]


def convert(blood_type):
    return BLOOD_TYPES[blood_type]


def main(recipient="A+", donor="O-"):
    """Run the protocol once and return the output bit.

    ``recipient`` is Alice's private input and ``donor`` is Bob's private
    input; the protocol outputs 1 when the donor's blood can be given to the
    recipient.
    """
    x, y = convert(recipient), convert(donor)
    dealer = Dealer()
    alice = Alice(x, dealer.RandA())
    bob = Bob(y, dealer.RandB())
    bob.Receive(alice.Send())
    alice.Receive(bob.Send())
    z = alice.Output()
    ostring = "compatible, i.e. B can donate to A" if z == 1 else "not compatible"
    print(f"The two blood types are {ostring}")
    return z


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 3:
        try:
            main(sys.argv[1], sys.argv[2])
        except KeyError as exc:
            valid = ", ".join(BLOOD_TYPES)
            raise SystemExit(
                f"unknown blood type {exc.args[0]!r}\nexpected one of: {valid}"
            ) from None
    else:
        raise SystemExit(f"usage: {sys.argv[0]} [RECIPIENT DONOR]")
