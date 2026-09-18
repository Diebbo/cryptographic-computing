package main

import "math/rand"

// MultShare is one party's share of a Beaver triple. The two parties' shares
// satisfy (aA xor aB) AND (bA xor bB) == (cA xor cB).
type MultShare struct {
	u, v, w bool
}

// Dealer hands out the randomness: one mask per input bit, and one triple per
// AND gate. It is trusted — this is the passively secure setting, so it is
// allowed to know every secret.
type Dealer struct {
	rng *rand.Rand
}

var dealer *Dealer

func initDealer(seed int64) {
	dealer = &Dealer{rng: rand.New(rand.NewSource(seed))}
}

func (d *Dealer) randBit() bool {
	return d.rng.Intn(2) == 1
}

// GiveInputMask returns the mask used to secret-share one input bit.
func (d *Dealer) GiveInputMask() bool {
	return d.randBit()
}

// GiveMultTriple returns both parties' shares of a fresh triple (u, v, w) with
// w = u AND v, itself XOR-shared between them. Call it once per AND gate.
func (d *Dealer) GiveMultTriple() (alice, bob MultShare) {
	var u, v, w bool
	u, v = d.randBit(), d.randBit()
	w = u && v
	m1, m2, m3 := d.randBit(), d.randBit(), d.randBit()
	return MultShare{u != m1, v != m2, w != m3}, MultShare{m1, m2, m3}
}
