import hashlib
import random
import secrets

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


_lambda = 128  # security parameter
LAMBDA_BYTES = _lambda // 8  # e.g. 16

class Gate:
    def __init__(self, input_wires, output_wire, operation, id):
        self.input_wires = input_wires
        self.output_wire = output_wire
        self.operation = operation
        self.id = id

class Wire:
    def __init__(self, i, k0, k1):
        self.i = i
        self.k0 = k0
        self.k1 = k1

def H(label_l: int, label_r: int, gate_id: int) -> int:
    data = (
        label_l.to_bytes(LAMBDA_BYTES, "big")
        + label_r.to_bytes(LAMBDA_BYTES, "big")
        + gate_id.to_bytes(4, "big")
    )
    digest = hashlib.sha256(data).digest()[:LAMBDA_BYTES]  # truncate to label size
    return int.from_bytes(digest, "big")

def generate_ciphertexts():
    ciphertexts = []
    for a in range(2):  # Alice's bit
        for b in range(2):  # Bob's bit
            out_label = out[a & b]  # AND gate; swap for other gates
            ct = H(wire_L[f"k{a}"], wire_R[f"k{b}"], i) ^ out_label
            ciphertexts.append(ct)

    random.shuffle(ciphertexts)
    return ciphertexts

class Garbler(Player):
    def garble_circuit_blood_compatibility(self, _lambda):
        """
        for each gate we have two input wires, one output, one id, 4
        ciphertexts, the operation.
        """
        translation_list = []  # for each id we have the key i.e. swap = 1, no
        # swap = 0
        C = {"wires": [], "gates": []}
        wire_counter = 0
        node_counter = 0
        # 1. input wires: we generate for each wire two random values of
        # the security parameter and the wire id, one for 0 and one for 1. We
        # also generate a random key for each wire.
        for _ in range(self.input_bits) * 2:
            # seamingly rando values of lambda bits
            k0, k1 = random.getrandbits(_lambda), random.getrandbits(_lambda)
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
        # i.e Alice is w0, w2, w4. Bob's w1, w3, w5

        # or bitwise and with alice's input bits
        for i in range(self.input_bits):  # 1, 2, 3
            wire_L = C["wires"][i * 2]  # alice's input wire
            wire_R = C["wires"][i * 2 + 1]  # bob's input wire

            # output wire labels (one per possible output bit)
            out = [secrets.randbits(_lambda), secrets.randbits(_lambda)]

            ciphertexts = []
            for a in range(2):  # Alice's bit
                for b in range(2):  # Bob's bit
                    out_label = out[a | b]  # OR gate; swap for other gates
                    ct = H(wire_L[f"k{a}"], wire_R[f"k{b}"], i) ^ out_label
                    ciphertexts.append(ct)

            random.SystemRandom().shuffle(ciphertexts)

            output_wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            node = {
                "input_wires": [f"w{i*2}", f"w{i*2+1}"],
                "ciphertexts": ciphertexts,
                "operation": "and",
                "gate_id": f"n{node_counter}",
                "output_wire": output_wire,
            }
            C.gates.append(node)
            C["wires"].append(output_wire)
        # make the and of all of the gates
        output_gates = []
        for i in range(len(C["gates"]) - 1):
            wire_L = C["gates"][i]["output_wire"]
            wire_R = C["gates"][i + 1]["output_wire"]
            k0, k1 = random.getrandbits(_lambda), random.getrandbits(_lambda)
            ciphertexts = []
            for j in range(2):  # alice's input bit
                for k in range(2):
                    ciphertext = hashlib.sha256(
                        wire_L[f"k{j}"].k0.to_bytes(16, "big")
                        + wire_R[f"k{j}"].k0.to_bytes(16, "big")
                    ) ^ (k0 + b"\x00" * _lambda)
                    ciphertexts.append(ciphertext)

            # shuffle the ciphertexts to hide the order of the inputs
            ciphertexts = random.sample(ciphertexts, len(ciphertexts))  # do I
            # trust copilot?

            output_wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            node = {
                "input_wires": [f"w{i*2}", f"w{i*2+1}"],
                "ciphertexts": ciphertexts,
                "operation": "and",
                "gate_id": f"n{node_counter}",
                "output_wire": output_wire,
            }
            output_gates.append(node)
            C["wires"].append(output_wire)

        C["gates"] += output_gates
        self.attributes["F"] = C
        return C


class Evaluator(Player):
    def eval(self):
        pass


def oblivious_transfer_of_input_bits(Alice, Bob):
    """
    oblivious trasfer protocol between Alice and Bob, where Alice has a bit,
    and Bob has m0 and m1. Those m0 and m1 are the lables at position 0, 2, 4 of
    the input gates of the garblign circuit.
    """

    def OT(m0, m1, b):
        return m0 if b == 0 else m1

    for i in range(len(Alice.input_bits)):
        alice_bit = int(Alice.input_bits[i])
        alice_input_wire = Bob.attributes["F"]["wires"][i * 2]
        m0, m1 = alice_input_wire["k0"], alice_input_wire["k1"]
        Alice.attributes[f"alice_label_{i}"] = OT(m0, m1, alice_bit)


if __name__ == "__main__":
    # bob runs
    Alice = Evaluator(input_bits="110")
    Bob = Garbler(input_bits="001")
    Bob.garble_circuit_blood_compatibility(_lambda)  # F, ex, et, d

    Alice.recv(Bob.send(["F", "d"]))

    # compute Y
    Bob.compute_Y()
    Alice.recv(Bob.send("Y"))

    # OT on alice bits
    oblivious_transfer_of_input_bits(Alice, Bob)

    # runs
    Alice.eval()
    z = Alice.decode()
    print(f"The two blood types are {'compatible, i.e. B can donate to A' if
          z == 1 else 'not compatible'}")
