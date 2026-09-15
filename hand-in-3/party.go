package main

type Party struct {
	Name    string
	IsAlice bool
	dealer  *Dealer
	shares  map[int]bool // nodeID -> this party's XOR-share of that wire
}

func NewParty(name string, isAlice bool, dealer *Dealer) *Party

// Phase 1 of Beaver multiplication — purely local. Each party blinds its
// shares of x and y with its own share of the triple. The resulting
// (d, e) must be exchanged with the other party before phase 2.
func (p *Party) PrepareMult(t MultShare, xShare, yShare bool) (d, e bool)

// Phase 2 — purely local, once d and e are opened. Exactly one of the two
// parties (by convention Alice) sets addCrossTerm, otherwise the d*e term
// is counted twice.
func (p *Party) FinishMult(t MultShare, d, e bool, addCrossTerm bool) bool
