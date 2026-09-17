package main

import (
	"errors"
	"fmt"
)

// Each input bit is masked with a dealer bit: the owner keeps the mask as
// its share, the other party receives (bit xor mask).
func InitInputs(alice, bob *Party,
	xNodes []*Node, x []bool, yNodes []*Node, y []bool,
) {
	if len(xNodes) != len(x) || len(yNodes) != len(y) {
		panic(fmt.Sprintf("InitInputs: %d x-nodes, %d x-bits, %d y-nodes, %d y-bits", len(xNodes), len(x), len(yNodes), len(y)))
	}

	for i, bit := range x {
		// NOTE: this operatio is supposed to be done by the player, for
		// practicality we will assume the dealer is honest
		mask := dealer.GiveInputMask()
		alice.shares[xNodes[i].ID] = mask
		bob.shares[xNodes[i].ID] = bit != mask
	}

	for j, bit := range y {
		mask := dealer.GiveInputMask()
		alice.shares[xNodes[j].ID] = bit != mask
		bob.shares[xNodes[j].ID] = mask
	}
}

// Walks the DAG once and returns both parties' shares of the node's value.
// Memoised in each party's `shares` map, so shared subexpressions are
// evaluated (and charged a triple) only once.
func EvalNode(alice, bob *Party, n *Node) error {
	if n == nil {
		return errors.New("EvalNode: nil node")
	}

	// Leaves (InputA/InputB) have nil children, so only recurse if a
	// child actually exists.
	if n.L != nil {
		if err := EvalNode(alice, bob, n.L); err != nil {
			return err
		}
	}
	if n.R != nil {
		if err := EvalNode(alice, bob, n.R); err != nil {
			return err
		}
	}

	switch n.Op {
	case InputA, InputB:
		// leaf: value already set during InitInputs, nothing to eval
		return nil
	case ConstGate:
		alice.Const(n.ID, n.ConstVal)
		bob.Const(n.ID, n.ConstVal)
	case Xor:
		alice.Xor(n.ID, n.L.ID, n.R.ID)
		bob.Xor(n.ID, n.L.ID, n.R.ID)
	case XorConst:
		// only Alice xors with the const value, Bob xors with false
		alice.XorConst(n.ID, n.L.ID, n.ConstVal)
		bob.XorConst(n.ID, n.L.ID, false)
	case And:
		if err := evalAndGate(alice, bob, n); err != nil {
			return err
		}
	default:
		return fmt.Errorf("EvalNode: unknown gate %v", n.Op)
	}

	return nil
}

func evalAndGate(alice, bob *Party, n *Node) error {
	if n.L == nil || n.R == nil {
		return fmt.Errorf("evalAndGate: And node %v missing child", n.ID)
	}

	// 1. get random values from dealer
	tripleAlice, tripleBob := dealer.GiveMultTriple()

	// 2. precompute d and e
	aD, aE := alice.PrepareMult(tripleAlice, alice.shares[n.L.ID], alice.shares[n.R.ID])
	bD, bE := bob.PrepareMult(tripleBob, bob.shares[n.L.ID], bob.shares[n.R.ID])

	// 3. secretly open d and e (in this simplified setting, just exchange them)
	zA := alice.FinishMult(tripleAlice, aD, bE, alice.shares[n.L.ID], alice.shares[n.R.ID])
	zB := bob.FinishMult(tripleBob, bD, aE, bob.shares[n.L.ID], bob.shares[n.R.ID])

	alice.shares[n.ID] = zA
	bob.shares[n.ID] = zB
	return nil
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
