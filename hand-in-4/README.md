# Hand-in 4 — Private matching / oblivious transfer from ElGamal

## The idea

Alice and Bob each hold a 3-bit input. At the end of the protocol, Alice learns a
single bit while Bob learns nothing about Alice's input, and Alice learns nothing beyond that one
bit — in particular, not which other candidates Bob marked as compatible.

The construction is a 1-out-of-8 oblivious transfer, built from ElGamal with **fake ("lossy") public keys**. Alice hides
her input inside a set of 8 public keys: one real key, whose secret exponent she
knows, and 7 fake keys that are indistinguishable from real ones and whose
discrete logarithms nobody knows. Bob encrypts an answer for every possible
index; only the ciphertext under Alice's real key can be decrypted by her.

## Protocol

1. **Alice — key generation.** Map her input to an index in `0..7`. Generate
   8 ElGamal public keys: at her index a real key `pk = g^sk` (keeping `sk`),
   at the other 7 indices fake keys `pk = r² mod p`, where `r` is drawn like an
   exponent and then thrown away. Send all 8 keys to Bob.
2. **Bob — messages.** For every candidate index `i`, encrypt the message
   `m = 1` if his input is a bitwise subset of candidate `i`, and `m = g`
   otherwise. Each of the 8 encryptions uses fresh randomness. Send the
   ciphertexts back.
3. **Alice — output.** Decrypt only the ciphertext at her own index. She gets
   `1` exactly when Bob's input is compatible with hers, and outputs that as a
   boolean.

**Why it works** (security against semi-honest parties):

- _Alice's privacy:_ real keys (`g^sk`, `sk` uniform) and fake keys (`r²`,
  `r` uniform) are both uniform over the subgroup of quadratic residues, so
  under DDH Bob cannot tell which index Alice chose.
- _Bob's privacy:_ Alice only knows the discrete logarithm of the single real
  key, so she can open exactly one ciphertext. Under the fake keys the message
  is masked by an exponent she cannot invert, and she learns nothing about the
  other 7 entries.

## Technical specifications

- **Group.** 1024-bit safe prime `p = 2q + 1` with `q` prime
  (`generateSafePrime`); generator `g = h² mod p` for random `h`, so `g` has
  order `q` and generates the subgroup of quadratic residues.
- **Randomness.** `Gen` / `OGen` / `Encrypt` receive a random integer of
  `n + λ` bits (`n = 1024`, `λ = 128`), reduced into `[1, p-1]` as
  `r mod (p-1) + 1`. The bias of this reduction is negligible (≈ 2⁻¹²⁸).
- **ElGamal.**
  - `Gen(r) → (sk = x, pk = g^x mod p)`
  - `OGen(r) → r² mod p` (fake key, no discrete log known)
  - `Encrypt(m, pk, r) → (c1 = g^r, c2 = m · pk^r mod p)`
  - `Decrypt(c, sk) → c2 · (c1^sk)⁻¹ mod p`
- **Messages.** `1` for compatible and `g` for incompatible. Both are quadratic
  residues, so `c2` is always in the QR subgroup — using a non-residue (e.g.
  `-1`) would leak the message bit to anyone via the Legendre symbol.
- **Compatibility predicate.** `isCompatible(a, b) = ⋀ᵢ (aᵢ ∨ ¬bᵢ)`, which is
  true iff `b ⊆ a`. Bob evaluates it with Alice's candidate as `a` and his own
  input as `b`, so Alice learns whether Bob's bits are covered by hers.
- **Reproducibility.** Fixed RNG seeds (Alice `57748`, Bob `808`) make runs
  deterministic. A debug trace of the whole protocol is printed to stdout.

## Files

| file         | contents                                                                 |
| ------------ | ------------------------------------------------------------------------ |
| `main.go`    | wires the protocol together                                              |
| `elgamal.go` | safe-prime setup and ElGamal (`Gen`, `OGen`, `Encrypt`, `Decrypt`)       |
| `parties.go` | Alice's and Bob's roles                                                  |
| `util.go`    | 3-bit encoding (`Bits`, `bitsToIndex`, `indexToBits`) and `isCompatible` |
| `ai.md`      | AI usage declaration                                                     |

## Run

```sh
go run .
```

Each run generates a fresh 1024-bit safe prime (a few seconds) and prints the
generated keys, Bob's eight encrypted candidates, and Alice's decrypted output.
