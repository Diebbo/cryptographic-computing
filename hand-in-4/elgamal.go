package main

import (
	"crypto/rand"
	"math/big"
)

type ElGamal struct {
	p, q, g *big.Int
}

type Ciphertext struct {
	c1 *big.Int
	c2 *big.Int
}

func generateSafePrime(bits int) (*big.Int, *big.Int) {
	for {
		// q must be 1023 bits so that p = 2q + 1 is 1024 bits.
		q, err := rand.Prime(rand.Reader, bits-1)
		if err != nil {
			return nil, nil
		}

		// p = 2q + 1
		p := new(big.Int).Lsh(q, 1)
		p.Add(p, big.NewInt(1))

		// Check that p is prime.
		if p.ProbablyPrime(64) {
			return p, q
		}
	}
}

func initElGamal(n, seed int) *ElGamal {
	p, q := generateSafePrime(n)
	var g *big.Int

	for {
		h, err := rand.Int(rand.Reader, new(big.Int).Sub(p, big.NewInt(3)))
		if err != nil {
			panic(err)
		}
		h.Add(h, big.NewInt(2))
		// g = h^2 mod p such that has order q
		g = new(big.Int).Exp(h, big.NewInt(2), p)

		// Avoid g = 1.
		if g.Cmp(big.NewInt(1)) != 0 {
			break
		}
	}

	return &ElGamal{
		p: p,
		q: q,
		g: g,
	}
}

func (e *ElGamal) parseRandom(r *big.Int) *big.Int {
	pm1 := new(big.Int).Sub(e.p, big.NewInt(1))
	x := new(big.Int).Mod(r, pm1)
	x.Add(x, big.NewInt(1))

	return x
}

func (e *ElGamal) Gen(r *big.Int) (*big.Int, *big.Int) {
	x := e.parseRandom(r)

	// pk = g^x mod p
	pk := new(big.Int).Exp(e.g, x, e.p)

	return x, pk
}

func (e *ElGamal) OGen(r *big.Int) *big.Int {
	x := e.parseRandom(r)
	return new(big.Int).Exp(x, big.NewInt(2), e.p)
}

func (e *ElGamal) Encrypt(m, pk, r *big.Int) *Ciphertext {
	x := e.parseRandom(r)
	// c1 = g^x mod p
	c1 := new(big.Int).Exp(e.g, x, e.p)

	// pk^x mod p
	pkR := new(big.Int).Exp(pk, x, e.p)

	// c2 = m * pk^x mod p
	c2 := new(big.Int).Mul(m, pkR)
	c2.Mod(c2, e.p)

	return &Ciphertext{
		c1: c1,
		c2: c2,
	}
}

func (e *ElGamal) Decrypt(ct *Ciphertext, sk *big.Int) *big.Int {
	// s = c1^sk mod p
	s := new(big.Int).Exp(ct.c1, sk, e.p)

	// Compute s^(-1) mod p
	sInv := new(big.Int).ModInverse(s, e.p)

	// m = c2 * s^(-1) mod p
	m := new(big.Int).Mul(ct.c2, sInv)
	m.Mod(m, e.p)

	return m
}
