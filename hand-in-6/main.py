import hashlib
import random

"""
implementation of the blood compatibility function with garbler circuits

function compatible(a, b):
    return a and not (b)
"""

"""
takes as input a function and a security parameter and return F , encoding information e, and decoding information d.
"""


class Player:
    def __init__(self, input_bits):
        self.input_bits = input_bits
        self.attributes = {}

    def recv(self, msg):
        self.attributes.update(msg)

    def send(self, msg):
        return (
            self.attributes[msg]
            if isinstance(msg, str)
            else [self.attributes[m] for m in msg]
        )


class Garbler(Player):
    def garble_circuit_blood_compatibility(self, lamda):
        """
        for each gate we have two input wires, one output, one id, 4
        ciphertexts, the operation.
        """
        translation_list = []  # for each id we have the key i.e. swap = 1, no
        # swap = 0
        C = {"wires": [], "nodes": []}
        wire_counter = 0
        node_counter = 0
        # 1. input wires: we generate for each wire two random values of
        # the security parameter and the wire id, one for 0 and one for 1. We
        # also generate a random key for each wire.
        for _ in range(self.input_bits) * 2:
            # seamingly rando values of lambda bits
            k0, k1 = random.getrandbits(lamda), random.getrandbits(lamda)
            swap = random.randint(0, 1)
            if swap == 1:
                k0, k1 = k1, k0
            translation_list.append({"id": f"w{wire_counter}", "swap": swap})
            wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            wire_counter += 1

            C.append(wire)

        # NOTE: 1. remember to negate bob's input bits when computing Y
        # INFO: I'll use the convention that one input wire is alice and the
        # next is bob

        # or bitwise and with alice's input bits
        for i in range(self.input_bits):  # 1, 2, 3
            wire_L = C["wires"][i * 2]  # alice's input wire
            wire_R = C["wires"][i * 2 + 1]  # bob's input wire
            # compute all of the possible outputs and add the masking
            k0, k1 = random.getrandbits(lamda), random.getrandbits(lamda)
            ciphertexts=[]
            for j in range(2):  # alice's input bit
                for k in range(2):
                    #TODO: check this shit
                    ciphertext = (
                            hashlib.sha256(wire_L[f"k{j}"].k0.to_bytes(16, "big") +
                            wire_R[f"k{j}"].k0.to_bytes(16, "big")) ^ (k0 ||
                                                                       "0"*lamda)
                            )
                    ciphertexts.append(ciphertext)

            # shuffle the ciphertexts to hide the order of the inputs
            ciphertexts = random.sample(ciphertexts, len(ciphertexts)) # do I
            # trust copilot?

            output_wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            node = {
                "input_wires": [f"w{i*2}", f"w{i*2+1}"],
                "ciphertexts": ciphertexts,
                "operation": "and",
                "node_id": f"n{node_counter}",
                "output_wire": output_wire,
            }
            C.nodes.append(node)
            C["wires"].append(output_wire)

        # make the and of all of the nodes
        output_nodes = []
        for i in range(len(C["nodes"]) - 1):
            wire_L = C["nodes"][i]["output_wire"]
            wire_R = C["nodes"][i + 1]["output_wire"]
            k0, k1 = random.getrandbits(lamda), random.getrandbits(lamda)
            ciphertexts=[]
            for j in range(2):  # alice's input bit
                for k in range(2):
                    ciphertext = (
                            hashlib.sha256(wire_L[f"k{j}"].k0.to_bytes(16, "big") +
                            wire_R[f"k{j}"].k0.to_bytes(16, "big")) ^ (k0 ||
                                                                       "0"*lamda)
                            )
                    ciphertexts.append(ciphertext)

            # shuffle the ciphertexts to hide the order of the inputs
            ciphertexts = random.sample(ciphertexts, len(ciphertexts)) # do I
            # trust copilot?
            
            output_wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            node = {
                "input_wires": [f"w{i*2}", f"w{i*2+1}"],
                "ciphertexts": ciphertexts,
                "operation": "and",
                "node_id": f"n{node_counter}",
                "output_wire": output_wire,
            }
            output_nodes.append(node)
            C["wires"].append(output_wire)

        C["nodes"] += output_nodes
        return C


class Evaluator(Player):
    def eval(self):
        pass


"""
oblivious trasfer protocol between Alice and Bob, where Alice has two messages
m0 and m1, and Bob has a choice bit b.
"""


def oblivious_transfer(Player_A, Player_B):
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
