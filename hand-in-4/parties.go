package main

import (
	"fmt"
	"math/big"
	"math/rand"
)

type Alice struct {
	input  Bits
	pks    [8]*big.Int
	sk     *big.Int
	rng    *rand.Rand
	output bool
	pke    *ElGamal
	lambda int
}

type Bob struct {
	input  Bits
	pks    [8]*big.Int
	rng    *rand.Rand
	pke    *ElGamal
	lambda int
}

func initAlice(input Bits, seed int64, pke *ElGamal, lambda int) *Alice {
	return &Alice{
		input:  input,
		rng:    rand.New(rand.NewSource(seed)),
		pke:    pke,
		lambda: lambda,
	}
}

// randBits returns a uniform random integer in [0, 2^n).
func randBits(rng *rand.Rand, n int) *big.Int {
	bound := new(big.Int).Lsh(big.NewInt(1), uint(n))
	return new(big.Int).Rand(rng, bound)
}

// fp returns a short hex fingerprint of a big.Int, for readable debug output.
func fp(x *big.Int) string {
	s := fmt.Sprintf("%x", x)
	if len(s) > 12 {
		return s[:12] + "..."
	}
	return s
}

func (a *Alice) GeneratePks() {
	n := a.pke.p.BitLen()
	real := bitsToIndex(a.input)
	fmt.Printf("Alice: real key at index %d\n", real)
	for i := 0; i < 8; i++ {
		r := randBits(a.rng, n+a.lambda)
		if i == real {
			sk, pk := a.pke.Gen(r)
			a.pks[i] = pk
			a.sk = sk
			fmt.Printf("Alice: pk[%d] = %s (real)\n", i, fp(pk))
		} else {
			a.pks[i] = a.pke.OGen(r)
			fmt.Printf("Alice: pk[%d] = %s (fake)\n", i, fp(a.pks[i]))
		}
	}
}

func (a *Alice) SendPks() [8]*big.Int {
	return a.pks
}

func (a *Alice) ReceiveMessages(messages [8]*Ciphertext) {
	idx := bitsToIndex(a.input)
	ct := messages[idx]
	m := a.pke.Decrypt(ct, a.sk)
	a.output = m.Cmp(big.NewInt(1)) == 0
	if a.output {
		fmt.Printf("Alice: ct[%d] decrypts to 1 -> compatible\n", idx)
	} else {
		fmt.Printf("Alice: ct[%d] decrypts to %s (not 1) -> not compatible\n", idx, fp(m))
	}
}

func (a *Alice) GetOutput() bool {
	return a.output
}

func initBob(input Bits, seed int64, pke *ElGamal, lambda int) *Bob {
	return &Bob{
		input:  input,
		rng:    rand.New(rand.NewSource(seed)),
		pke:    pke,
		lambda: lambda,
	}
}

func (b *Bob) ReceivePks(pks [8]*big.Int) {
	b.pks = pks
	fmt.Printf("Bob: received pks")
	for i, pk := range pks {
		fmt.Printf(" [%d]=%s", i, fp(pk))
	}
	fmt.Println()
}

func (b *Bob) GenerateMessages() [8]*Ciphertext {
	messages := [8]*Ciphertext{}
	for i := 0; i < 8; i++ {
		var m *big.Int
		r := randBits(b.rng, b.pke.p.BitLen()+b.lambda)
		compatible := isCompatible(indexToBits(i), b.input)
		if compatible {
			m = big.NewInt(1)
		} else {
			m = new(big.Int).Set(b.pke.g) // g is in QR
		}
		ciphertext := b.pke.Encrypt(m, b.pks[i], r)
		messages[i] = ciphertext
		fmt.Printf("Bob: candidate %v (idx %d) compatible=%v m=%s ct=(c1=%s, c2=%s)\n",
			indexToBits(i), i, compatible, fp(m), fp(ciphertext.c1), fp(ciphertext.c2))
	}
	return messages
}
