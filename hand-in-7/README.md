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

Where
- γ is the bit-length of the integers in the public key
- η is the bit-length of the secret key (which is the hidden approximate-gcd of all the public-key integers)
- ρ is the bit-length of the noise (i.e., the distance between the public key elements and the nearest multiples of the secret key), and
- τ is the number of integers in the public key.

`MEDIUM` is the default. Key generation is slow; switch to `TOY` for quick runs.

# On the parameters choice

The parameters have been taken from the paper [CLT13], referenced in the lecture notes. Each of the parameters choices grants that the scheme is "homomorphic enough" for our circuit, since it only has multiplication depth of 3, while these parameters can work up to depth 4. In general, the scheme can support multiplication depth up to $d$, where:

```math
d \leq \left\lfloor \log_2 \left(\frac{\eta}{\rho + 1 + \log_2(\tau)}\right) \right\rfloor
```

## On the subset S choice
We decide to choose the subset S for encryption tossing a random coin for each $y$ in the public key. The expected size of the subset is $τ/2$, while the case where there is no encryption applied ($|S| = 0$) happens with probability $1 / 2^τ$, which is negligible in $λ$.

## Usage

```sh
python main.py   # run the protocol on a sample input
python test.py   # test the homomorphic gates (AND, XOR, OR, NOT, ORNOT)
```

The full test over all 64 input combinations is commented out at the bottom of `main.py` because it is slow.
