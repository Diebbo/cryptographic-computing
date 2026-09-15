package main

import (
	"math/rand"
)

// One party's share of a triple. The two parties' shares satisfy
// (aA xor aB) AND (bA xor bB) == (cA xor cB).
type MultShare struct {
	A, B, C bool
}

type Dealer struct {
	rng *rand.Rand
}

func NewDealer(seed int64) *Dealer

func (d *Dealer) randBit() bool
func (d *Dealer) split(v bool) (sA, sB bool) // sA xor sB == v

func (d *Dealer) GiveInputMask() bool
func (d *Dealer) GiveMultTriple() (alice, bob MultShare) // one per AND gate
