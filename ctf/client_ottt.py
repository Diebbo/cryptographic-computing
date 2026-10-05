"""
Exercise: one-time truth tables.

Bob has a pass phrase, chosen at random for every connection. For each character of it you
run one OTTT execution of the equality function: you guess a character and learn only
whether the guess was right. Each execution uses its own fresh output from the trusted
dealer. At the end you send Bob the whole pass phrase, and if it is right he hands over his secret message.

You play Alice. Find the flaw in the protocol, recover the pass phrase within a single
connection and get Bob's message.

To run: `python3 client_ottt.py` talks to the server.

The Bob class below is the same as what runs on the server, so may be useful for
experimentation.
"""

import secrets

from crycom import chars, receive_message, send_message
from pwn import *

n = 5  # bits per execution, which is enough to hold one character
size = 2**n

# The public function: Alice guesses one character of Bob's pass phrase and the protocol
# tells her only whether the guess was right.
T = [[1 if i == j else 0 for j in range(size)] for i in range(size)]


class Dealer:
    """The trusted dealer of the OTTT protocol, played here by the server. One fresh
    dealer output per execution - the protocol is only good for a single use."""

    def __init__(self) -> None:
        self.r = secrets.randbelow(size)
        self.s = secrets.randbelow(size)
        # M_B masks the shifted truth table, and M_A is what is left for Alice
        self.M_B = [[0] * size for _ in range(size)]
        self.M_A = [
            [
                self.M_B[i][j] ^ T[(i - self.r) % size][(j - self.s) % size]
                for j in range(size)
            ]
            for i in range(size)
        ]


class Alice:
    """Alice is the guesser. She receives (r, M_A) from the dealer, sends u = x + r,
    and learns f(x, y) and nothing else."""

    def __init__(self, guess, r, M_A) -> None:
        self.x = guess
        self.r = r
        self.M_A = M_A

    def send(self):
        self.u = (self.x + self.r) % size
        return self.u

    def output(self, v, z_B):
        # M_A[u][v] XOR M_B[u][v] is T[x][y] by construction, and z_B is Bob's half of it
        return self.M_A[self.u][v] ^ z_B


class Bob:
    """Bob holds the pass phrase. He receives (s, M_B) from the dealer, and answers
    with v = y + s and his share z_B of the output."""

    def __init__(self, y, dealer) -> None:
        self.y = y
        self.s = dealer.s
        self.M_B = dealer.M_B

    def respond(self, u):
        v = (self.y + self.s) % size
        return v, self.M_B[u][v]


phrase_length = 20


def bobs_setup():
    # A fresh pass phrase for every connection, so that guessing it over many runs gets
    # nowhere: Alice has to recover it within a single run
    bobs_secret = "".join(secrets.choice(chars) for _ in range(phrase_length))
    # one execution per character, each with its own dealer output
    dealers = [Dealer() for _ in bobs_secret]
    return (
        bobs_secret,
        dealers,
        [Bob(chars.index(c), dealer) for c, dealer in zip(bobs_secret, dealers)],
    )


# What Bob hands over to whoever knows the pass phrase. This is the message you should
# recover, replaced with an empty string here
bobs_message = "ciaociaooooo"


# -------------------YOUR SOLUTION HERE-------------------
# Override the steps of the honest Alice you want to change,
# and then modify (or copy) run() to use it.
class MaliciousAlice(Alice):
    pass


def run():
    with remote("chals.syssec.dk", 15006) as rem:
        print("Protocol started")

        # Round 1: the preprocessing the dealer hands to Alice
        material = receive_message(rem)
        print(f"Received the dealer output for {len(material)} executions")

        # Round 2: one guess per character of Bob's pass phrase
        guess = "c"
        guessers = [Alice(chars.index(guess), r, M_A) for r, M_A in material]
        send_message([guesser.send() for guesser in guessers], rem)
        print("Sent the masked guesses")

        # Round 3: Bob's masked inputs and output shares
        answers = receive_message(rem)
        outputs = [
            guesser.output(v, z_B) for guesser, (v, z_B) in zip(guessers, answers)
        ]
        print(f"Guessed '{guess}' in every position, and the answers were:", outputs)

        # Round 4: claim the pass phrase, keeping the guess wherever it was right
        send_message("".join(guess if hit else " " for hit in outputs), rem)
        print("Bob's reply:", receive_message(rem))


if __name__ == "__main__":
    run()
