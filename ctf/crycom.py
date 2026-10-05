"""
Helper code for the Cryptographic Computing exercises.
"""

import json
import secrets
import struct
import sys

from typing import Tuple


# ----------------------------------------------------------------- text encoding

# Messages are written in this alphabet and read as a number in base 27.
chars = " abcdefghijklmnopqrstuvwxyz"
base = len(chars)

def str_to_int(s):
    n = 0
    for c in s:
        n = n * base + chars.index(c)
    return n

def int_to_str(n):
    s = ""
    if n == 0:
        return chars[0]
    while n > 0:
        n, rem = divmod(n, base)
        s = chars[rem] + s
    return s

def str_to_bits(s):
    return [int(b) for b in bin(str_to_int(s))[2:]] if s else []

def bits_to_str(bits):
    return int_to_str(int("".join(str(b) for b in bits), 2)) if bits else ""


# -------------------------------------------------------------- the blood types

# Encoding of the 3 bit input:
# 1st bit = true if party X has A
# 2nd bit = true if party X has B
# 3rd bit = true if party X has +
lookup_table = [[1,0,0,0,0,0,0,0],
            [1,1,0,0,0,0,0,0],
            [1,0,1,0,0,0,0,0],
            [1,1,1,1,0,0,0,0],
            [1,0,0,0,1,0,0,0],
            [1,1,0,0,1,1,0,0],
            [1,0,1,0,1,0,1,0],
            [1,1,1,1,1,1,1,1]]

def lookup_index(bitarray):
    return int("".join(str(i) for i in bitarray), 2)

def lookup_fct(R, D):
    indR = lookup_index(R)
    indD = lookup_index(D)
    return lookup_table[indR][indD]


# ------------------------------------------------------------------- randomness

def secure_shuffle(items):
    """Shuffle a list in place using the system CSPRNG. The secrets module exposes no
    shuffle of its own, so this is Fisher-Yates over secrets.randbelow."""
    for i in range(len(items) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]


# --------------------------------------------------------------- number theory

def egcd(a: int, b: int) -> Tuple[int, int, int]:
    """Extended GCD: returns (g, x, y) with ax + by = g = gcd(a,b)."""
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a: int, m: int) -> int:
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"No modular inverse for {a} mod {m}")
    return x % m

def is_probable_prime(n: int, k: int = 12) -> bool:
    """Miller-Rabin primality test. k rounds - more rounds -> more accuracy."""
    if n < 2:
        return False
    for small in [2,3,5,7,11,13,17,19,23,29,31]:
        if n % small == 0:
            return n == small
    # write n-1 as d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    def trial_composite(a: int) -> bool:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return False
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return False
        return True  # n is definitely composite

    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2  # random in [2, n-2]
        if trial_composite(a):
            return False
    return True

def generate_prime(bits: int) -> int:
    """Generate a probable prime of 'bits' bits."""
    while True:
        # set highest and lowest bits to ensure correct size and oddness
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate

def legendre(a, n):
    """The Legendre symbol of a, computed like a gcd rather than with Euler's criterion."""
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


# ----------------------------------------------------------- the ElGamal group

# p = 2**2048 - 2**1984 - 1 + 2**64 * (np.floor(2**1918*math.pi) + 124476), a safe prime.
# 2 is a quadratic residue modulo p, so g generates the subgroup of order q.
p = 32317006071311007300338913926423828248817941241140239112842009751400741706634354222619689417363569347117901737909704191754605873209195028853758986185622153212175412514901774520270235796078236248884246189477587641105928646099411723245426622522193230540919037680524235519125679715870117001058055877651038861847280257976054903569732561526167081339361799541336476559160368317896729073178384589680639671900977202194168647225871031411336429319536193471636533209717077448227988588565369208645296636077250268955505928362751121174096972998068410554359584866583291642136218231078990999448652468262416972035911852507045361090559
q = (p-1)//2
g = 2

def int_to_group(x):
    """Encode an integer as a group element, by taking whichever of +(x+1), -(x+1) is
    a quadratic residue. This is method 3 from the appendix."""
    if legendre(x+1, p) == 1:
        return (x + 1) % p
    else:
        return (-x - 1) % p

def group_to_int(x):
    if x <= q:
        return (x - 1) % p
    else:
        return (-x - 1) % p

def str_to_group(s):
    return int_to_group(str_to_int(s))

def group_to_str(x):
    return int_to_str(group_to_int(x))


# ------------------------------------------------------------------- Paillier

class PubKey:
    def __init__(self, N: int):
        self.N = N
        self.N_sq = N * N

class PrivKey:
    def __init__(self, sk: int):
        self.sk = sk

def keygen(bits: int = 1024) -> Tuple[PubKey, PrivKey]:
    """Generate a keypair:
       - choose primes p,q, N = p*q
       - compute phi = (p-1)*(q-1)
       - compute k = modinv(phi mod N, N)
       - set sk = k * phi (so sk = 0 (mod phi) and sk = 1 (mod N))
       - the public key is N
    """
    half = bits // 2
    prime1 = generate_prime(half)
    prime2 = generate_prime(bits - half)
    while prime2 == prime1:
        prime2 = generate_prime(bits - half)
    N = prime1 * prime2
    phi = (prime1 - 1) * (prime2 - 1)
    k = modinv(phi % N, N)  # k such that phi * k = 1 (mod N)
    return PubKey(N), PrivKey(k * phi)

def encrypt(pub: PubKey, m: int) -> int:
    """Encrypt m in Z_N, returning a ciphertext mod N^2."""
    N, N_sq = pub.N, pub.N_sq
    if not (0 <= m < N):
        raise ValueError("m must be in Z_N (0 <= m < N)")
    # random r in Z_N^* (a uniform r in Z_N is in Z_N^* with overwhelming probability)
    r = secrets.randbelow(N)
    return ((1 + m * N) % N_sq) * pow(r, N, N_sq) % N_sq

def decrypt(pub: PubKey, priv: PrivKey, c: int) -> int:
    """Decrypt a ciphertext mod N^2 and return the plaintext in Z_N."""
    N, N_sq, sk = pub.N, pub.N_sq, priv.sk
    if not (0 <= c < N_sq):
        raise ValueError("ciphertext must be in Z_{N^2}")
    u = pow(c, sk, N_sq)
    # u is 1 + m*N*sk (mod N^2)
    t = (u - 1) // N
    return t * modinv(sk % N, N) % N

def e_add(pub: PubKey, c1: int, c2: int) -> int:
    """Homomorphic addition of plaintexts: multiply the ciphertexts."""
    return (c1 * c2) % pub.N_sq

def e_mul_const(pub: PubKey, c: int, k: int) -> int:
    """Homomorphic scalar multiplication: E(m)^k = E(k*m)."""
    return pow(c, k, pub.N_sq)


# ------------------------------------------------------------------- messaging

# Every message on the wire is its length as four big endian bytes, then that many bytes
# of JSON. Anything longer than this is refused rather than allocated.
max_message = 8 * 1024 * 1024

class StdioTube:
    """Gives a server the same send/recvn interface that pwntools gives the client, so
    both sides of every exercise can use the same two functions below."""
    def __init__(self):
        self.rbuf = sys.stdin.buffer
        self.wbuf = sys.stdout.buffer

    def send(self, data):
        self.wbuf.write(data)
        self.wbuf.flush()

    def recvn(self, n):
        data = b''
        while len(data) < n:
            chunk = self.rbuf.read(n - len(data))
            if not chunk:
                raise EOFError("the other side closed the connection")
            data += chunk
        return data

def send_message(msg, conn):
    payload = json.dumps(msg).encode()
    conn.send(struct.pack('>I', len(payload)) + payload)

def receive_message(conn):
    (length,) = struct.unpack('>I', conn.recvn(4))
    if length > max_message:
        raise ValueError(f"refusing a message of {length} bytes")
    return json.loads(conn.recvn(length))
