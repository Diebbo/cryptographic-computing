from secrets import randbits
from itertools import product

P_BITS = 2128
Q_BITS = 8_500_000
R_BITS =  56
N = 2410

TOY_P_BITS = 988
TOY_Q_BITS = 290_000
TOY_R_BITS = 26
TOY_N = 188

def generate_dhe_keys():
    p = randbits(P_BITS - 1) << 1 | 1
    y = [p * randbits(Q_BITS) + 2 * randbits(R_BITS) for _ in range(N)]
    return (p, y)

def encrypt(pk, m):
    c = m
    for y in pk:
        c += y * randbits(1)
    return c

def decrypt(sk, c):
    return (c % sk) % 2


class Player:
    def __init__(self, bits):
        self.bits = bits

    def init_dhe(self):
        sk, pk = generate_dhe_keys()
        self.sk = sk
        self.pk = pk

    def send_pk(self):
        return self.pk

    def receive_pk(self, pk):
        self.pk = pk

    def encrypt_bits(self):
        return [encrypt(self.pk, i) for i in self.bits]

    def receive_encrypted_bits(self, bits):
        self.x_bits = bits

    def evaluate_blood_compatibility(self):
        y_bits = self.encrypt_bits()
        x_bits = self.x_bits

        def AND(c1, c2):
            return c1 * c2

        def XOR(c1, c2):
            return c1 + c2

        def OR(c1, c2):
            return c1 + c2 + c1*c2

        def NOT(c1):
            return XOR(c1, encrypt(self.pk, 1))

        def ORNOT(c1, c2):
            return OR(c1, NOT(c2))

        output = AND(
            AND(ORNOT(x_bits[0], y_bits[0]),
                ORNOT(x_bits[1], y_bits[1])),
            ORNOT(x_bits[2], y_bits[2])
        )
        self.output = output
        return output

    def receive_output(self, output):
        self.output = output

    def decrypt_output(self):
        return decrypt(self.sk, self.output)


def test_inputs(a, b):
    return (a[0] | (1 - b[0])) & (a[1] | (1 - b[1])) & (a[2] | (1 - b[2]))


def test_protocol(sk, pk, a_input, b_input):
    Alice = Player(a_input)
    Bob = Player(b_input)

    Alice.sk = sk
    Alice.pk = pk

    Bob.receive_pk(Alice.send_pk())

    Bob.receive_encrypted_bits(Alice.encrypt_bits())

    Alice.receive_output(Bob.evaluate_blood_compatibility())

    z = Alice.decrypt_output()

    return z == test_inputs(a_input, b_input)


if __name__ == "__main__":

    Alice = Player([1, 0, 1])
    Bob = Player([0, 1, 1])

    Alice.init_dhe()

    print("Keys have been generated")

    Bob.receive_pk(Alice.send_pk())

    Bob.receive_encrypted_bits(Alice.encrypt_bits())

    Alice.receive_output(Bob.evaluate_blood_compatibility())

    z = Alice.decrypt_output()

    print(f"The two blood types are {'compatible, i.e. B can donate to A' if
          z == 1 else 'not compatible'}")

    # for testing purpose only, we reuse the keys, since they are too slow to be generated at every iteration
    # i = 0
    # sk = Alice.sk
    # pk = Alice.pk

    # for a_input, b_input in product(product([0, 1], repeat=3), repeat=2):
    #     i += 1
    #     print(f"Testing {i}/64", a_input, b_input)
    #     assert test_protocol(sk, pk, a_input, b_input), f"Failed for inputs {a_input} and {b_input}"

    # print("All tests passed!")

    # tests are commented because they take too much time
