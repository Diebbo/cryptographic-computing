

Alice genera 7 chiave fake: ( (n + lambda) bits ) mod (p-1) + 1
        e una vera sk
Bob encrypta con le chiavi
Alice decrypta la chiave vera

La chiave vera corrisponde al vero input di Alice
Bob computa tutte i possibili input di Alice e critta con chiave corrispondente



x Alice input, y Bob input
Alice needs:
GeneratePks(x)

Send pk

Bob needs:
receive pk
Compute(y, pk)
Enc(m, r, pk)



ElGamal
        init: set p, q, g where p = 2q + 1
        get_params() return p, q, g
        Gen(g, p, q) return sk, g^sk
        OGen(p) return r^2 mod p
        encrypt(pk, m, r = None) return (g^r, m * h^r)
        decrypt(sk, c) {
                c1, c2 = C
                return c2 * c1^(-sk)
        }




////////
main

alice genera 7 chiavi fake e una vera

alice manda le chiavi pubbliche a bob

bob computa tutti i possibili output usando tutti i possibili input di alice

bob critta tutti i messaggi con la corrispettiva chiave pubblica

bob manda i messaggi crittati

alice decritta il messaggio corrispondente al suo input



//////
Alice e Bob hanno lo stesso ElGamal condiviso
Generano la loro randomness e la passano a elgamal per crittare o generare



