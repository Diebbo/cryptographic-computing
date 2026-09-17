package main

import "fmt"

// Each input bit is masked with a dealer bit: the owner keeps the mask as
// its share, the other party receives (bit xor mask).
func InitInputs(alice, bob *Party, dealer *Dealer,
	xNodes []*Node, x []bool, yNodes []*Node, y []bool,
) {
	if len(xNodes) != len(x) || len(yNodes) != len(y) {
		panic(fmt.Sprintf("InitInputs: %d x-nodes, %d x-bits, %d y-nodes, %d y-bits", len(xNodes), len(x), len(yNodes), len(y)))
	}

	for i, bit := range x {
		mask := dealer.GiveInputMask()
		alice.shares[xNodes[i].ID] = mask
		bob.shares[xNodes[i].ID] = bit != mask
	}
}

// Walks the DAG once and returns both parties' shares of the node's value.
// Memoised in each party's `shares` map, so shared subexpressions are
// evaluated (and charged a triple) only once.
func EvalNode(alice, bob *Party, n *Node) (shareA, shareB bool) {
	// recursively check left and right and then eval current
	if n == nil {
		panic("EvalNode: nil node")
	}
	// recurr on Node's left and right children if they exist
	EvalNode(alice, bob, n.L)
	EvalNode(alice, bob, n.R)

	switch n.Op {
	case InputA:
	case InputB:
		return alice.shares[n.ID], bob.shares[n.ID]
	case ConstGate:
		return n.ConstVal, n.ConstVal
	case Xor:
		return alice.shares[n.L.ID] != bob.shares[n.R.ID], bob.shares[n.L.ID] != alice.shares[n.R.ID]
	case XorConst:
		return alice.shares[n.L.ID] != n.ConstVal, bob.shares[n.L.ID] != n.ConstVal
	case And:
		return evalAndGate(alice, bob, n)
	}
	panic(fmt.Sprintf("EvalNode: unknown gate %v", n.Op))
}

func evalAndGate(alice, bob *Party, n *Node) (bool, bool) {
	// 1. get random values from dealer
	var tripleAlice, tripleBob MultShare
	tripleAlice, tripleBob = alice.dealer.GiveMultTriple()
	// 2. precompute d and e
	aD, aE := alice.PrepareMult(tripleAlice, alice.shares[n.L.ID], alice.shares[n.R.ID])
	bD, bE := bob.PrepareMult(tripleBob, bob.shares[n.L.ID], bob.shares[n.R.ID])
	// 3. secretly open d and e (in this simplified setting, just exchange them)
	zA := alice.FinishMult(tripleAlice, aD, bE, alice.shares[n.L.ID], alice.shares[n.R.ID])
	zB := bob.FinishMult(tripleBob, bD, aE, bob.shares[n.L.ID], bob.shares[n.R.ID])
	return zA, zB
}

// plaintextCompat is the ground truth for the target function: the AND over all
// bit positions of OrNot(x_i, y_i). (x_i or not y_i) is false exactly when x_i
// is false and y_i is true, so the conjunction holds iff no position has that
// pattern.
//
// SPECS.md files this under eval.go next to EvalNode; it lives here for now
// because nothing outside the tests calls it yet.
func plaintextCompat(x, y []bool) bool {
	if len(x) != len(y) {
		panic("plaintextCompat: length mismatch")
	}
	for i := range x {
		if !x[i] && y[i] {
			return false
		}
	}
	return true
}
