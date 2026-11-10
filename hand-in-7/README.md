# Hand-in 7: Blood Type Compatibility with Homomorphic Encryption

A two-party protocol where Bob checks whether he can donate blood to Alice without learning her blood type. It uses the DGHV "FHE over the integers" scheme.

## How it works

1. Alice generates a key pair (`sk = p`, `pk = [y_1, ..., y_N]`) and sends `pk` to Bob.
2. Alice encrypts her 3 blood type bits and sends them to Bob.
3. Bob encrypts his own bits and homomorphically evaluates
   `(x0 ∨ ¬y0) ∧ (x1 ∨ ¬y1) ∧ (x2 ∨ ¬y2)`
   using `XOR = +` and `AND = *`.
4. Alice decrypts the result with `(c mod p) mod 2`. A `1` means Bob can donate to Alice.

## Parameters

Set in `main.py` (`R_BITS, P_BITS, Q_BITS, N`):

| Name   | λ  | ρ  | η    | γ         | τ    |
|--------|----|----|------|-----------|------|
| TOY    | 42 | 26 | 988  | 290,000   | 188  |
| SMALL  | 52 | 41 | 1558 | 1,600,000 | 661  |
| MEDIUM | 62 | 56 | 2128 | 8,500,000 | 2410 |

`MEDIUM` is the default. Key generation is slow; switch to `TOY` for quick runs.

## Usage

```sh
python main.py   # run the protocol on a sample input
python test.py   # test the homomorphic gates (AND, XOR, OR, NOT, ORNOT)
```

The full test over all 64 input combinations is commented out at the bottom of `main.py` because it is slow.
