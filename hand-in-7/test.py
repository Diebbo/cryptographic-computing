from secrets import randbits
from itertools import product

P_BITS = 2128
Q_BITS = 8_500_000
R_BITS =  56
N = 2410

def generate_dhe_keys():
    p = randbits(P_BITS - 1) << 1 | 1
    y = [p * randbits(Q_BITS) + 2*randbits(R_BITS) for _ in range(N)]
    return (p, y)



sk, pk = generate_dhe_keys()

print("Keys generated")

def encrypt(m):
    c = m
    for y in pk:
        c += y * randbits(1)
    return c

def decrypt(c):
    return (c % sk) % 2

def AND(c1, c2):
    return c1 * c2

def XOR(c1, c2):
    return c1 + c2

def OR(c1, c2):
    return c1 + c2 + c1*c2

def NOT(c1):
    return XOR(c1, encrypt(1))

def ORNOT(c1, c2):
            return OR(c1, NOT(c2))


def test_inputs(a, b):
    return (a[0] | (1 - b[0])) & (a[1] | (1 - b[1])) & (a[2] | (1 - b[2]))

def test_AND():
     for a in [0,1]:
          for b in [0,1]:
               c1, c2 = encrypt(a), encrypt(b)
               c3 = AND(c1, c2)
               d3 = decrypt(c3)
               if d3 != (a * b):
                    print("AND test failed with", a, b, d3)

test_AND()