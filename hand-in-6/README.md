# Hand-in 6 - Blood compatibility with garbled circuits

## The idea

Alice (the recipient) and Bob (the donor) each hold a 3-bit blood type, one bit
per antigen. Bob can donate to Alice if Bob has no antigen that Alice is missing:

```
f(x, y) = AND_i ( x_i OR NOT y_i )
```

Alice learns `f(x, y)` and nothing else. Bob learns nothing.

Bob (the garbler) garbles a circuit for `f`. Alice (the evaluator) gets one
label per input wire, evaluates the garbled circuit and decodes only the final
output.

## Files

- `garbled_circuit.py`: circuit, garbling, evaluation, the protocol and tests.
- `elgamal.py`: ElGamal encryption and decryption used for the oblivious
  transfer.

## Circuit

`BuildCompatibilityCircuit` builds the circuit as a tree of gates:

```
AND( AND( OR(x0, NOT y0), OR(x1, NOT y1) ), OR(x2, NOT y2) )
```

Each gate is also the wire that carries its output. The supported gates are
AND, OR and XOR. NOT is built as `XOR(y, 1)`, where `1` is a constant wire.
The constant wire has a single label, since it only ever carries the value 1,
and that label is included in the garbled circuit.

## Garbling

Every wire gets two random λ-bit labels `k0, k1` (λ = 128) sampled with
`secrets`. For a gate with id `id`, input wires `L, R` and output wire `O`,
Bob builds one ciphertext per input combination `(a, b)`:

```
C_ab = H(L_a, R_b, id) XOR ( O_{g(a,b)} || 0^λ )
```

`H` is SHA-256, so its output is 2λ bits. The ciphertexts of each gate are
shuffled.

`GarbleCircuit` walks the circuit and returns a tree of `GarbledGate`s that
holds only gate ids, the structure and the ciphertexts. The only label it
contains is the one of the constant wire. The decoding information `d` is the
pair of labels of the output wire.

## Protocol

1. Bob garbles the circuit and sends Alice the garbled circuit `F`, the labels
   for his own input bits, the ids of Alice's input wires and `d`.
2. For each of her input bits, Alice gets the label for her bit by a 1-out-of-2
   oblivious transfer based on ElGamal:
   - Alice samples a secret key `sk` and sets `pk_b = g^sk`. For the other
     bit she samples `pk_{1-b}` obliviously, as a random square mod `p`, so
     she does not know its secret key.
   - Bob encrypts label `k0` under `pk_0` and label `k1` under `pk_1` and
     sends both ciphertexts.
   - Alice can decrypt only `c_b`, which gives her the label for her bit.
     Bob cannot tell which of the two keys is the real one, so he learns
     nothing about `b`.
3. Alice evaluates the circuit from the leaves up. At each gate she computes
   `H(L, R, id)` from the two labels she holds and XORs it with each of the
   four ciphertexts. Exactly one result ends in λ zero bits; its first λ bits
   are the output label. A wrong row passes this check with probability about
   2^-λ.
4. Alice looks up the output label in `d` and gets the output bit.

Alice holds exactly one label per wire and never sees which bit it stands for,
except on the output wire.

## Limitations

- The protocol is secure only against semi-honest parties.
- Both parties run in the same process and "send" messages by calling each
  other's methods.

## Running

```
python3 garbled_circuit.py
```

The program runs the protocol on the inputs set at the bottom of the file,
prints whether the blood types are compatible, and then checks the result
against the plaintext function for all 64 input pairs.
