package main

import "math/rand"

// MultShare is one party's share of a Beaver triple. The two parties' shares
// satisfy (aA xor aB) AND (bA xor bB) == (cA xor cB).
type MultShare struct {
	A, B, C bool
}

// Dealer hands out the randomness: one mask per input bit, and one triple per
// AND gate. It is trusted — this is the passively secure setting, so it is
// allowed to know every secret.
type Dealer struct {
	rng *rand.Rand
}

func NewDealer(seed int64) *Dealer {
	panic("TODO: NewDealer")
}

func (d *Dealer) randBit() bool {
	panic("TODO: Dealer.randBit")
}

// split returns two bits whose XOR is v.
func (d *Dealer) split(v bool) (sA, sB bool) {
	panic("TODO: Dealer.split")
}

// GiveInputMask returns the mask used to secret-share one input bit.
func (d *Dealer) GiveInputMask() bool {
	panic("TODO: Dealer.GiveInputMask")
}

// GiveMultTriple returns both parties' shares of a fresh triple (a, b, c) with
// c = a AND b, itself XOR-shared between them. Call it once per AND gate.
func (d *Dealer) GiveMultTriple() (alice, bob MultShare) {
	panic("TODO: Dealer.GiveMultTriple")
}
