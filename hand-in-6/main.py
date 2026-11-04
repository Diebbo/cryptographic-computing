import hashlib
import os
import random
import secrets

DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def debug(*args):
    if DEBUG:
        print("[DEBUG]", *args)


def short(label: int) -> str:
    """first 8 hex chars of a label, enough to tell labels apart"""
    return f"{label:032x}"[:8]


# debug only: copy of Bob's secret label table, so debug prints can show which
# bit a label stands for. Alice never reads this in the protocol itself.
_DEBUG_LABELS = {}


def label_bit(wire_id, label):
    """debug only: which bit a label stands for on a wire (Alice can't do this)"""
    wire = _DEBUG_LABELS[wire_id]
    if label == wire["k0"]:
        return 0
    if label == wire["k1"]:
        return 1
    return "?"

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
        keys = [msg] if isinstance(msg, str) else msg
        return {k: self.attributes[k] for k in keys}


_lambda = 128  # security parameter
LAMBDA_BYTES = _lambda // 8  # e.g. 16
ZERO_PAD = b"\x00" * LAMBDA_BYTES


def H(label_l: int, label_r: int, gate_id: int) -> bytes:
    """hash to 2*lambda bits (sha256 = 32 bytes = 2 * LAMBDA_BYTES)"""
    data = (
        label_l.to_bytes(LAMBDA_BYTES, "big")
        + label_r.to_bytes(LAMBDA_BYTES, "big")
        + gate_id.to_bytes(4, "big")
    )
    return hashlib.sha256(data).digest()


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def encrypt(label_l: int, label_r: int, gate_id: int, out_label: int) -> bytes:
    """C = H(L, R, id) XOR (out_label || 0^lambda)"""
    plaintext = out_label.to_bytes(LAMBDA_BYTES, "big") + ZERO_PAD
    return xor(H(label_l, label_r, gate_id), plaintext)


def decrypt(label_l: int, label_r: int, gate_id: int, ct: bytes):
    """returns the output label if the padding is all zeros, otherwise None"""
    plaintext = xor(H(label_l, label_r, gate_id), ct)
    if plaintext[LAMBDA_BYTES:] != ZERO_PAD:
        return None
    return int.from_bytes(plaintext[:LAMBDA_BYTES], "big")


class Garbler(Player):
    def garble_circuit_blood_compatibility(self, _lambda):
        """
        for each gate we have two input wires, one output, one id, 4
        ciphertexts, the operation.
        """
        # C is what Alice receives: only the topology and the ciphertexts.
        # labels is Bob's private table wire id -> (k0, k1), never sent.
        C = {"nodes": []}
        labels = {}
        wire_counter = 0
        node_counter = 0
        # 1. input wires: we generate for each wire two random values of
        # the security parameter and the wire id, one for 0 and one for 1. We
        # also generate a random key for each wire.
        for _ in range(len(self.input_bits) * 2):
            # seamingly rando values of lambda bits
            k0, k1 = secrets.randbits(_lambda), secrets.randbits(_lambda)
            wire = {"id": f"w{wire_counter}", "k0": k0, "k1": k1}
            wire_counter += 1

            labels[wire["id"]] = wire
            owner = "alice" if (wire_counter - 1) % 2 == 0 else "bob"
            debug(
                f"input wire {wire['id']} ({owner} bit {(wire_counter - 1) // 2}):"
                f" k0={short(k0)} k1={short(k1)}"
            )

        # NOTE: 1. remember to negate bob's input bits when computing Y
        # INFO: I'll use the convention that one input wire is alice and the
        # next is bob
        # i.e Alice is w0, w2, w4. Bob's w1, w3, w5

        # or bitwise and with alice's input bits
        for i in range(len(self.input_bits)):  # 1, 2, 3
            wire_L = labels[f"w{i * 2}"]  # alice's input wire
            wire_R = labels[f"w{i * 2 + 1}"]  # bob's input wire

            # output wire labels (one per possible output bit)
            out = [secrets.randbits(_lambda), secrets.randbits(_lambda)]

            ciphertexts = []
            for a in range(2):  # Alice's bit
                for b in range(2):  # Bob's bit
                    out_label = out[a or b]  # OR gate
                    ct = encrypt(
                        wire_L[f"k{a}"], wire_R[f"k{b}"], node_counter, out_label
                    )
                    ciphertexts.append(ct)

            random.SystemRandom().shuffle(ciphertexts)

            output_wire = {"id": f"w{wire_counter}", "k0": out[0], "k1": out[1]}
            node = {
                "input_wires": [wire_L["id"], wire_R["id"]],
                "ciphertexts": ciphertexts,
                "operation": "or",
                "node_id": f"n{node_counter}",
                "output_wire": output_wire["id"],  # id only, no labels
            }
            C["nodes"].append(node)
            labels[output_wire["id"]] = output_wire
            debug(
                f"OR  gate {node['node_id']}: {node['input_wires'][0]} OR "
                f"{node['input_wires'][1]} -> {output_wire['id']}"
                f" (k0={short(out[0])} k1={short(out[1])})"
            )
            wire_counter += 1
            node_counter += 1
        # make the and of all of the nodes
        output_nodes = []

        wire_L = labels[C["nodes"][i]["output_wire"]]
        for i in range(len(C["nodes"]) - 1):
            wire_R = labels[C["nodes"][i]["output_wire"]]

            # output wire labels (one per possible output bit)
            out = [secrets.randbits(_lambda), secrets.randbits(_lambda)]

            ciphertexts = []
            for a in range(2):  # Alice's bit
                for b in range(2):  # Bob's bit
                    out_label = out[a & b]  # AND gate
                    ct = encrypt(
                        wire_L[f"k{a}"], wire_R[f"k{b}"], node_counter, out_label
                    )
                    ciphertexts.append(ct)

            random.SystemRandom().shuffle(ciphertexts)

            output_wire = {"id": f"w{wire_counter}", "k0": out[0], "k1": out[1]}
            node = {
                "input_wires": [wire_L["id"], wire_R["id"]],
                "ciphertexts": ciphertexts,
                "operation": "and",
                "node_id": f"n{node_counter}",
                "output_wire": output_wire["id"],  # id only, no labels
            }
            C["nodes"].append(node)
            labels[output_wire["id"]] = output_wire
            debug(
                f"AND gate {node['node_id']}: {node['input_wires'][0]} AND "
                f"{node['input_wires'][1]} -> {output_wire['id']}"
                f" (k0={short(out[0])} k1={short(out[1])})"
            )
            wire_counter += 1
            node_counter += 1
            wire_L = output_wire

        C["nodes"] += output_nodes
        C["output_wire"] = output_wire["id"]
        # d: decoding information, the two labels of the final output wire only
        d = {"k0": output_wire["k0"], "k1": output_wire["k1"]}
        self.attributes["F"] = C
        self.attributes["d"] = d
        self.attributes["labels"] = labels  # private, never sent
        if DEBUG:
            _DEBUG_LABELS.update(labels)
        return C, d

    def compute_Y(self):
        """
        compute the Y value of the garbled circuit, set of input lables
        associated with his bits that alice cannot decrypt
        """
        labels = self.attributes["labels"]
        # w1, w3, w5 are bob's input wires
        Y = []
        for i in range(len(self.input_bits)):
            bob_bit = int(self.input_bits[i])
            bob_input_wire = labels[f"w{i * 2 + 1}"]
            Y.append(bob_input_wire[f"k{1-bob_bit}"])
            # we flip the bits as we want to compute the not on his input values
            debug(
                f"Y[{i}]: bob bit {bob_bit} -> sends label for {1 - bob_bit}"
                f" on {bob_input_wire['id']} ({short(Y[-1])})"
            )
        self.attributes["Y"] = Y
        return Y


class Evaluator(Player):
    def eval(self):
        # map wire id -> the one label Alice holds for it
        # (Alice's inputs are w0, w2, w4; Bob's are w1, w3, w5)
        labels = {}
        for i, x in enumerate(self.attributes["X"]):
            labels[f"w{2 * i}"] = x
        for i, y in enumerate(self.attributes["Y"]):
            labels[f"w{2 * i + 1}"] = y
        self.attributes["labels"] = labels

        for node in self.attributes["F"]["nodes"]:
            input_wires = node["input_wires"]
            input_labels = [labels[input_wires[0]], labels[input_wires[1]]]
            gate_id = int(node["node_id"][1:])
            # compute the hash with the input labels and the gate id and check
            # between the computed hash and the ciphertexts to find the output
            # label
            # only the right row decrypts to label || 0^lambda; the other three
            # give random-looking padding (false positive prob. 2^-lambda)
            for ct in node["ciphertexts"]:
                output_label = decrypt(
                    input_labels[0], input_labels[1], gate_id, ct
                )
                if output_label is not None:
                    out_id = node["output_wire"]
                    labels[out_id] = output_label
                    if DEBUG:
                        in_bits = [label_bit(w, labels[w]) for w in input_wires]
                        debug(
                            f"eval {node['node_id']}: "
                            f"{input_wires[0]}={in_bits[0]}, "
                            f"{input_wires[1]}={in_bits[1]} -> "
                            f"{out_id}={label_bit(out_id, output_label)}"
                        )
                    break
            else:
                raise ValueError(f"no ciphertext decrypted for {node['node_id']}")

    def decode(self):
        """
        decode the output label to get the output bit
        """
        output_wire = self.attributes["F"]["output_wire"]
        output_label = self.attributes["labels"][output_wire]
        d = self.attributes["d"]
        debug(f"decode: output wire {output_wire} label {short(output_label)}")
        if output_label == d["k0"]:
            return 0
        elif output_label == d["k1"]:
            return 1
        else:
            raise ValueError("Invalid output label")


def oblivious_transfer_of_input_bits(Alice, Bob):
    """
    oblivious trasfer protocol between Alice and Bob, where Alice has a bit,
    and Bob has m0 and m1. Those m0 and m1 are the lables at position 0, 2, 4 of
    the input nodes of the garblign circuit.
    """

    def OT(m0, m1, b):
        return m0 if b == 0 else m1

    X = []
    for i in range(len(Alice.input_bits)):
        alice_bit = int(Alice.input_bits[i])
        alice_input_wire = Bob.attributes["labels"][f"w{i * 2}"]
        m0, m1 = alice_input_wire["k0"], alice_input_wire["k1"]
        lable = OT(m0, m1, alice_bit)
        X.append(lable)
        debug(
            f"OT X[{i}]: alice bit {alice_bit} on {alice_input_wire['id']}"
            f" ({short(lable)})"
        )

    Alice.attributes["X"] = X


if __name__ == "__main__":
    # bob runs
    Alice = Evaluator(input_bits="110")
    Bob = Garbler(input_bits="000")
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
