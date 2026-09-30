

Alice genera 7 chiave fake: ( (n + lambda) bits ) mod (p-1) + 1
        e una vera sk
Bob encrypta con le chiavi
Alice decrypta la chiave vera

La chiave vera corrisponde al vero input di Alice
Bob computa tutte i possibili input di Alice e critta con chiave corrispondente



x Alice input, y Bob input
Alice needs:
PreparePk(x)
Gen(sk)
OGen(r)
Send pk

Bob needs:
receive pk
Compute(y, pk)
Enc(m, r, pk)