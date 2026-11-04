import hashlib
import random
import secrets


_lambda = 128  # security parameter
LAMBDA_BYTES = _lambda // 8  # e.g. 16
ZERO_BYTES = b'\x00' * LAMBDA_BYTES

def generate_labels(n = 2):
    return [secrets.token_bytes(LAMBDA_BYTES) for v in range(n)]

def int_to_bytes(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")

def xor(a,b):
    return bytes(x ^ y for x, y in zip(a, b))

class Gate:
    counter_id = 0

    def __init__(self, constant = False, map = None, left = None, right = None): #constant wires are all 1 (no need to have a 0 wire)
        self.id = Gate.counter_id
        Gate.counter_id += 1

        self.map = map
        self.left = left
        self.right = right
        self.labels = generate_labels(2 if not constant else 1)
        self.values = [0, 1] if not constant else [1]

class GarbledGate:
    def __init__(self, id, left = None, right = None, ciphertexts = None, label = None):
        self.id = id
        self.left = left
        self.right = right
        self.ciphertexts = ciphertexts
        self.label = label

def AndGate(left, right):
    return Gate(False, lambda a,b: a & b, left, right)

def OrGate(left, right):
    return Gate(False,lambda a,b: a | b, left, right)

def XorGate(left, right):
    return Gate(False, lambda a,b: a ^ b, left, right)

def OneWire():
    return Gate(True, None, None, None)  # Constant wire with value 1

def NotGate(left):
    return XorGate(left, OneWire()) # NOT gate can be implemented as XOR with a constant 1 wire

def InputWire():
    return Gate(False, None, None, None)  # Input wire with values [0, 1]


def H(left, right, id) -> int:
    digest = hashlib.sha256(left + right + int_to_bytes(id)).digest()[:2*LAMBDA_BYTES]  # truncate to two label size
    return digest

def generate_ciphertexts(gate):
    ciphertexts = []
    for a, left_label in zip(gate.left.values, gate.left.labels):  # Alice's bit
        for b, right_label in zip(gate.right.values, gate.right.labels):  # Bob's bit
            _G = H(left_label, right_label, gate.id)  
            ct = xor(_G, gate.labels[gate.map(a, b)] + ZERO_BYTES)
            ciphertexts.append(ct)

    random.shuffle(ciphertexts)
    return ciphertexts

def GarbleCircuit(gate):
    if gate.left is None and gate.right is None:
        if gate.values == [0, 1]:
            return GarbledGate(gate.id, None, None, None, None)  # Input wire, no label yet
        else:
            return GarbledGate(gate.id, None, None, None, gate.labels[0]) # Constant wire, return the label for the constant value

    left_garbled = GarbleCircuit(gate.left)
    right_garbled = GarbleCircuit(gate.right)

    ciphertexts = generate_ciphertexts(gate)

    return GarbledGate(gate.id, left_garbled, right_garbled, ciphertexts, None)

 
def BuildCompatibilityCircuit():
    alice_inputs = [InputWire() for _ in range(3)]  # Alice's input wires
    bob_inputs = [InputWire() for _ in range(3)]  # Bob's input wires

    circuit = AndGate(
        AndGate(
            OrGate(alice_inputs[0], NotGate(bob_inputs[0])),
            OrGate(alice_inputs[1], NotGate(bob_inputs[1])),
            ),
            OrGate(alice_inputs[2], NotGate(bob_inputs[2])),
    )

    return circuit, alice_inputs, bob_inputs



class Player:
    def __init__(self, input_bits):
        self.input_bits = input_bits

class Garbler(Player):
    def garble_circuit_blood_compatibility(self):
        circuit, alice_inputs, bob_inputs = BuildCompatibilityCircuit()
        garbled_circuit = GarbleCircuit(circuit)

        self.circuit = circuit
        self.garbled_circuit = garbled_circuit
        self.alice_inputs = alice_inputs
        self.bob_inputs = bob_inputs

    def send_garbled_circuit(self):
        # Send the garbled circuit and the labels for Bob's input wires
        bob_labels = [(gate.id, gate.labels[int(bit)]) for gate, bit in zip(self.bob_inputs, self.input_bits)]
        alice_ids = [gate.id for gate in self.alice_inputs]
        decoder = self.circuit.labels
        return (self.garbled_circuit, bob_labels, alice_ids, decoder)

    def send_alice_labels(self):
        # Send the labels for Alice's input wires based on her input bits
        alice_labels = [(gate.id, gate.labels) for gate in self.alice_inputs]
        return alice_labels

class Evaluator(Player):
    def receive_garbled_circuit(self, garbled_circuit, bob_labels, alice_ids, output_labels):
        self.garbled_circuit = garbled_circuit
        self.bob_labels = {id: label for id, label in bob_labels}
        self.alice_ids = alice_ids
        self.output_labels = output_labels

    # TODO: implemente OT 
    def receive_alice_labels(self, alice_labels):
        self.alice_labels = {id: labels[bit] for (id, labels), bit in zip(alice_labels, self.input_bits)}

    def eval(self):
        # Evaluate the garbled circuit using the received labels
        def eval_gate(garbled_gate):
            if garbled_gate.left is None and garbled_gate.right is None:
                # Input wire or constant wire
                if garbled_gate.label is not None:
                    return garbled_gate.label  # Constant wire
                if garbled_gate.id in self.alice_ids:
                    return self.alice_labels[garbled_gate.id]
                else:
                    return self.bob_labels[garbled_gate.id]

            left_label = eval_gate(garbled_gate.left)
            right_label = eval_gate(garbled_gate.right)

            # Find the correct ciphertext to decrypt
            _G = H(left_label, right_label, garbled_gate.id)
            for ct in garbled_gate.ciphertexts:
                attempt = xor(_G, ct)
                if attempt[-LAMBDA_BYTES:] == ZERO_BYTES:
                    return attempt[:-LAMBDA_BYTES]  # Return the label without the zero padding
            return None

        output_label = eval_gate(self.garbled_circuit)
        if output_label is None:
            return None
        output = self.output_labels.index(output_label)  # Find the index of the output label
        return output


# def oblivious_transfer_of_input_bits(Alice, Bob):
#     """
#     oblivious trasfer protocol between Alice and Bob, where Alice has a bit,
#     and Bob has m0 and m1. Those m0 and m1 are the lables at position 0, 2, 4 of
#     the input gates of the garblign circuit.
#     """

#     def OT(m0, m1, b):
#         return m0 if b == 0 else m1

#     for i in range(len(Alice.input_bits)):
#         alice_bit = int(Alice.input_bits[i])
#         alice_input_wire = Bob.attributes["F"]["wires"][i * 2]
#         m0, m1 = alice_input_wire["k0"], alice_input_wire["k1"]
#         Alice.attributes[f"alice_label_{i}"] = OT(m0, m1, alice_bit)


if __name__ == "__main__":
    Alice = Evaluator(input_bits=[1, 0, 0])
    Bob = Garbler(input_bits=[1, 0, 0])

    Bob.garble_circuit_blood_compatibility()  # F, ex, et, d

    Alice.receive_garbled_circuit(*Bob.send_garbled_circuit())

    Alice.receive_alice_labels(Bob.send_alice_labels())

    z = Alice.eval()

    print(f"The two blood types are {'compatible, i.e. B can donate to A' if
          z == 1 else 'not compatible'}")

def test_inputs(a, b):
    return (a[0] | (1 - b[0])) & (a[1] | (1 - b[1])) & (a[2] | (1 - b[2]))


def test_circuit(a_input, b_input):
    Alice = Evaluator(input_bits=a_input)
    Bob = Garbler(input_bits=b_input)

    Bob.garble_circuit_blood_compatibility()  # F, ex, et, d

    Alice.receive_garbled_circuit(*Bob.send_garbled_circuit())

    Alice.receive_alice_labels(Bob.send_alice_labels())
    # runs
    z = Alice.eval()
    return z == test_inputs(a_input, b_input)


from itertools import product

for a_input, b_input in product(product([0, 1], repeat=3), repeat=2):
    assert test_circuit(a_input, b_input), f"Failed for inputs {a_input} and {b_input}"

print("All tests passed!")