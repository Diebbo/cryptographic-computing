package main

// Party is one of the two participants. Its shares map holds this party's
// XOR-share of every wire it has evaluated, keyed by node ID — which doubles
// as the memo that keeps EvalNode from walking the DAG twice.
type Party struct {
	Name    string
	IsAlice bool
	dealer  *Dealer
	shares  map[int]bool
}

func NewParty(name string, isAlice bool, dealer *Dealer) *Party {
	panic("TODO: NewParty")
}

// PrepareMult is phase 1 of Beaver multiplication — purely local. The returned
// (d, e) must be opened with the other party before phase 2.
func (p *Party) PrepareMult(t MultShare, xShare, yShare bool) (d, e bool) {
	panic("TODO: Party.PrepareMult")
}

// FinishMult is phase 2 — purely local, run once d and e are open.
// addCrossTerm must be true for exactly one of the two parties.
func (p *Party) FinishMult(t MultShare, d, e bool, addCrossTerm bool) bool {
	panic("TODO: Party.FinishMult")
}
