import hashlib
import secrets

from crycom import p, g, legendre

_E = 256


def _v(x):
    if not (isinstance(x, int) and 1 < x < p and legendre(x, p) == 1):
        raise ValueError("bad group element")
    return x


def _g(i, x):
    d = hashlib.shake_256(f"g,{i},{x}".encode()).digest(288)
    return pow(int.from_bytes(d, 'big') % p, 2, p)


def _h(i, a, x, n):
    d = hashlib.shake_256(f"h,{i},{a},{x}".encode()).digest((n + 7) // 8)
    return int.from_bytes(d, 'big') >> (-n % 8)


class BaseOTSender:
    def __init__(self, n):
        self._n = n

    def send(self, R, pairs):
        if len(R) != len(pairs):
            raise ValueError("wrong number of OTs")
        a = 1 + secrets.randbelow(2**_E - 1)
        A = pow(g, a, p)
        out = []
        for i, ((r0, r1), (m0, m1)) in enumerate(zip(R, pairs)):
            _v(r0), _v(r1)
            out.append([m0 ^ _h(i, A, pow(r0 * _g(i, r1) % p, a, p), self._n),
                        m1 ^ _h(i, A, pow(r1 * _g(i, r0) % p, a, p), self._n)])
        return [A, out]


class BaseOTReceiver:
    def __init__(self, c, n):
        self._c = c
        self._n = n

    def choose(self):
        self._b = [1 + secrets.randbelow(2**_E - 1) for _ in self._c]
        R = []
        for i, (b, c) in enumerate(zip(self._b, self._c)):
            u = pow(2 + secrets.randbelow(p - 2), 2, p)
            w = pow(g, b, p) * pow(_g(i, u), -1, p) % p
            R.append([w, u] if c == 0 else [u, w])
        return R

    def receive(self, msg):
        A, e = msg
        _v(A)
        if len(e) != len(self._c):
            raise ValueError("wrong number of OTs")
        return [e[i][c] ^ _h(i, A, pow(A, self._b[i], p), self._n)
                for i, c in enumerate(self._c)]
