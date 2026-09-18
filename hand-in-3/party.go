package main

import "math/rand"

// Party is one of the two participants. Its shares map holds this party's
// XOR-share of every wire it has evaluated, keyed by node ID — which doubles
// as the memo that keeps EvalNode from walking the DAG twice.
type Party struct {
	Name    string
	IsAlice bool
	shares  map[int]bool
	rng     *rand.Rand
}

func NewParty(name string, isAlice bool, seed int64) *Party {
	return &Party{
		Name:    name,
		IsAlice: isAlice,
		shares:  make(map[int]bool),
		rng:     rand.New(rand.NewSource(seed)),
	}
}

// PrepareMult is phase 1 of the multiplication — purely local. The returned
// (d, e) must be opened with the other party before phase 2.
func (p *Party) PrepareMult(t MultShare, xShare, yShare bool) (d, e bool) {
	// u and v are given in the multishare
	// [d] = [x] + [u], [e] = [y] + [v], where + is sum mod 2
	d = t.u != xShare
	e = t.v != yShare
	return d, e
}

func (p *Party) randBit() bool {
	return p.rng.Intn(2) == 1
}

func (p *Party) split(v bool) (sA, sB bool) {
	mask := p.randBit()
	return (mask != v), mask
}

// FinishMult is phase 2 — purely local, run once d and e are open.
// addCrossTerm must be true for exactly one of the two parties.
func (p *Party) FinishMult(t MultShare, d, e, xShare, yShare bool) bool {
	// [z] = [w]+e[x]+d[y]−de
	return t.w != (e && xShare) != (d && yShare) != (d && e)
}

func (p *Party) Xor(ID, LeftID, RightID int) {
	p.shares[ID] = p.shares[LeftID] != p.shares[RightID]
}

func (p *Party) XorConst(ID, LeftID int, Value bool) {
	p.shares[ID] = p.shares[LeftID] != Value
}

func (p *Party) AndConst(ID, LeftID int, Value bool) {
	p.shares[ID] = p.shares[LeftID] && Value
}

func (p *Party) Const(ID int, Value bool) {
	p.shares[ID] = Value
}

func (p *Party) SendOutputShare(ID int) bool {
	return p.shares[ID]
}

func (p *Party) SendOutput(ID int) bool {
	return p.shares[ID]
}

func (p *Party) ReceiveOutputShare(ID int, Value bool) {
	p.shares[ID] = p.shares[ID] != Value
}
