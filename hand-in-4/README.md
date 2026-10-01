

Alice genera 7 chiave fake: ( (n + lambda) bits ) mod (p-1) + 1
        e una vera sk
Bob encrypta con le chiavi
Alice decrypta la chiave vera

La chiave vera corrisponde al vero input di Alice
Bob computa tutte i possibili input di Alice e critta con chiave corrispondente



x Alice input, y Bob input
Alice needs:
GeneratePks(x)
Gen(g, p, q) return sk, g^sk
OGen(p) return r^2 mod p
Send pk

Bob needs:
receive pk
Compute(y, pk)
Enc(m, r, pk)



ElGamal
        init: set p, q, g where p = 2q + 1
        get_params() return p, q, g
        encrypt(pk, m, r = None) return (g^r, m * h^r)
        decrypt(sk, c) {
                c1, c2 = C
                return c2 * c1^(-sk)
        }


