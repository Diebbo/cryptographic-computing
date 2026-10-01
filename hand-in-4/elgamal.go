package main

import (
	"crypto/rand"
	"math"
	"math/big"
)

type ElGamal struct {
	p, q, g big.Int
}

func init(n, seed int) *ElGamal {
	// n is the bit-length of p
	// generate p with random
	var p, q big.Int
	q := rand.Prime(1023)
	for i := range 1000 {
		p = 2*q + 1
		if p.ProbablyPrime(20) {
			break
		}
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
