package main

import (
	"crypto/rand"
	"math"
	"math/big"
)

type ElGamal struct {
	p, q, g *big.Int
}

func generateSafePrime(bits int) (*big.Int, *big.Int, error) {
	for {
		// q must be 1023 bits so that p = 2q + 1 is 1024 bits.
		q, err := rand.Prime(rand.Reader, bits-1)
		if err != nil {
			return nil, nil, err
		}

		// p = 2q + 1
		p := new(big.Int).Lsh(q, 1)
		p.Add(p, big.NewInt(1))

		// Check that p is prime.
		if p.ProbablyPrime(64) {
			return p, q, nil
		}
	}
}

func initElGamal(n, seed int) *ElGamal {
	// n is the bit-length of p
	// generate p with random
	p, q, err := generateSafePrime(n)
	if err != nil {
		panic(err)
	}

	return &ElGamal{
		p: p,
		q: q,
		g: 2,
	}
}

func (e *ElGamal) randBit() bool {
	return p.rng.Intn(2) == 1
}

func (e *ElGamal) Gen(r int) (int, int) {
	rr := rand.Int(e.p - 1)[0] + 1
	return math.Pow(e.g, r) % e.p, (math.Pow(pk, r) * m) % e.p
}

func (e *ElGamal) Encrypt(m, pk int) (int, int) {
	r := rand.Int(e.p - 1)[0] + 1
	return math.Pow(e.g, r) % e.p, (math.Pow(pk, r) * m) % e.p
}

func (e *ElGamal) Decrypt(sk int, c int) int {
	r := rand.Int(p-1) + 1
	return math.Pow(g, r) % p, (math.Pow(h, r) * m) % p
}

func (e *ElGamal) Retrieve() bool {
	return p.rng.Intn(2) == 1
}
