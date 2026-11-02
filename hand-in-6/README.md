# Hand-in 6 - Private matching MPC with garbled circuits

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
