"""
implementation of the blood compatibility function with garbler circuits

function compatible(a, b):
    return a and not (b)
"""

"""
takes as input a function and a security parameter and return F , encoding information e, and decoding information d.
"""


def garble_circuit(lamda, f):

    pass


def encode(e, x):
    pass


def decode(d, y):
    pass


def eval(F, X):
    pass


def compatible(a, b):
    pass


class Garbler:
    def garble_circuit_blood_compatibility(self, lamda):
        """
        for each gate we have two input wires, one output, one id, 4
        ciphertexts, the operation.
        """
        C = []
        w0 = {"k0": 0, "k1": 0}
        w1 = {"k0": 0, "k1": 0}
        output_node = {
            "input_wires": [w0, w1],  # ?
            "ciphertexts": [c0, c1, c2, c3],  # ?
        }
        C.append(output_node)
        return C


class Evaluator:
    pass


def oblivious_transfer():
    pass


if __name__ == "__main__":
    # bob runs
    Alice = Evaluator(input_bits="110")
    Bob = Garbler(input_bits="001")
    Bob.garble_circuit_blood_compatibility(128)  # F, ex, et, d

    Alice.recv(Bob.send(["F", "d"]))

    # compute Y
    Bob.compute_Y()
    Alice.recv(Bob.send("Y"))

    # OT on alice bits
    oblivious_transfer(Alice, Bob)

    # runs
    Alice.eval()
    z = Alice.decode()
    print(f"The two blood types are {'compatible, i.e. B can donate to A' if
          z == 1 else 'not compatible'}")
