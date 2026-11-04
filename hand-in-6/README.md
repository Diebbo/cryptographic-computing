# Hand-in 6 - Blood compatibility with garbled circuits

## The idea

Alice (the recipient) and Bob (the donor) each hold a 3-bit blood type, one bit
per antigen. Bob can donate to Alice if Bob has no antigen that Alice is missing:

```
f(x, y) = AND_i ( x_i OR NOT y_i )
```

Alice learns `f(x, y)` and nothing else. Bob learns nothing.

Bob garbles a circuit for `f`. Alice evaluates it on one label per wire and
decodes only the final output.

## Circuit

Wires `w0, w2, w4` are Alice's input bits and `w1, w3, w5` are Bob's.

```
n0: w0 OR w1 -> w6
n1: w2 OR w3 -> w7
n2: w4 OR w5 -> w8
n3: w8 AND w6 -> w9
n4: w9 AND w7 -> w10   (output)
```

The circuit has no NOT gate. Bob negates his own bits when he picks his input
labels, so each OR gate computes `x_i OR NOT y_i`.

## Garbling

For every wire Bob samples two random λ-bit labels `k0, k1` (λ = 128) with
`secrets`. For a gate with input wires `L, R` and output wire `O`, he builds
four ciphertexts, one per input combination `(a, b)`:

```
C_ab = H(L_a, R_b, gate_id) XOR ( O_{g(a,b)} || 0^λ )
```

`H` is SHA-256, so its output is 2λ bits. Bob shuffles the four ciphertexts.

The garbled circuit `F` that Alice receives contains only the gate structure
(wire ids) and the ciphertexts. The labels stay with Bob. The decoding
information `d` is the two labels of the output wire `w10`.

## Protocol

1. Bob garbles the circuit and sends `F` and `d` to Alice.
2. Bob sends `Y`, the labels for the negations of his bits on `w1, w3, w5`.
3. Alice gets `X`, the labels for her bits on `w0, w2, w4`, by oblivious
   transfer.
4. Alice evaluates the gates in order. For each gate she computes
   `H(L, R, gate_id)` from the two labels she holds and XORs it with each of
   the four ciphertexts. Exactly one result ends in λ zero bits; its first λ
   bits are the output label. A wrong row passes this check with probability
   about 2^-λ.
5. Alice compares the label on `w10` with `d` to get the output bit.

Alice holds exactly one label per wire and never sees which bit it stands for,
except on the output wire.

## Limitations

- The oblivious transfer in `oblivious_transfer_of_input_bits` is a
  placeholder. It hands Alice the label for her bit directly, so in this code
  Bob could see her input. A real OT (for example the ElGamal-based one from
  the previous hand-in) would replace it without changing the rest of the
  protocol.
- The protocol is secure only against semi-honest parties.

## Running

```
python3 main.py
DEBUG=true python3 main.py
```

The inputs are set at the bottom of `main.py`. With `DEBUG=true` the program
prints every label, every gate and the bit carried on each wire during
evaluation. These prints use a copy of Bob's labels and are not part of the
protocol.
