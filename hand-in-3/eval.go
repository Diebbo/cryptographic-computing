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
		a, b := alice.split(bit)
		fmt.Printf("InitInputs: x[%d] = %v, Alice share = %v, Bob share = %v\n", i, bit, a, b)
		alice.shares[xNodes[i].ID] = a
		bob.shares[xNodes[i].ID] = b
	}

	for j, bit := range y {
		b, a := bob.split(bit)
		fmt.Printf("InitInputs: y[%d] = %v, Alice share = %v, Bob share = %v\n", j, bit, a, b)
		alice.shares[yNodes[j].ID] = a
		bob.shares[yNodes[j].ID] = b
	}
}

// DebugEval turns the per-node trace on and off. It is on by default: when this
// protocol misbehaves, the only question worth asking is which wire diverged,
// and each printed line is exactly one wire. Only the tests, which call
// evalPlain and never EvalNode, are unaffected by it.
var DebugEval = false

// debugNode reports one wire after it has been evaluated: the gate that produced
// it, both parties' shares, and the value they reconstruct to (shareA xor
// shareB — the value a correctly implemented "open" would yield).
//
// It also flags a node whose share is missing from a party's map. That case is
// worth shouting about because a missing key reads back as false, i.e. it looks
// like a perfectly good wire carrying 0.
func debugNode(n *Node, alice, bob *Party) {
	if !DebugEval {
		return
	}

	a, aOK := alice.shares[n.ID]
	b, bOK := bob.shares[n.ID]

	// Leaves carry no operand information in their children, so spell out the
	// field that actually determines them.
	detail := ""
	switch n.Op {
	case InputA, InputB:
		detail = fmt.Sprintf("(input %d)  ", n.InputIdx)
	case ConstGate, XorConst, AndConst:
		detail = fmt.Sprintf("(const %v)  ", n.ConstVal)
	}

	warn := ""
	if !aOK || !bOK {
		warn = fmt.Sprintf("  <-- NO SHARE (A set=%v, B set=%v)", aOK, bOK)
	}

	fmt.Printf("[eval] node %2d  %-9s %sA=%v B=%v  value=%v%s\n",
		n.ID, n.Op, detail, a, b, a != b, warn)
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

	// add memoization: if the node has already been evaluated, return early
	if _, ok := alice.shares[n.ID]; ok {
		if _, ok := bob.shares[n.ID]; !ok {
			return fmt.Errorf("EvalNode: Alice has share for node %d but Bob does not", n.ID)
		}
		debugNode(n, alice, bob)
		return nil
	}

	switch n.Op {
	case InputA, InputB:
		// leaf: value already set during InitInputs, nothing to eval
		debugNode(n, alice, bob)
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

	debugNode(n, alice, bob)
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

	debugAnd(alice, bob, n, tripleAlice, tripleBob, aD, bD, aE, bE)

	// 3. secretly open d and e (in this simplified setting, just exchange them)
	zA := alice.FinishMult(tripleAlice, aD, bE, alice.shares[n.L.ID], alice.shares[n.R.ID])
	zB := bob.FinishMult(tripleBob, bD, aE, bob.shares[n.L.ID], bob.shares[n.R.ID])

	alice.shares[n.ID] = zA
	bob.shares[n.ID] = zB
	return nil
}

// debugAnd traces one Beaver multiplication: the triple the dealer handed out
// (reconstructed from the two shares, which is what the protocol actually sees)
// and the d and e the parties open from it.
//
// Two checks run alongside the printout, because both failures are silent
// otherwise — the gate still produces two shares that look plausible:
//
//   - the triple must satisfy c == a AND b, or the Beaver identity is wrong;
//   - the opened d and e must equal x xor a and y xor b, or a blind was applied
//     to the wrong operand.
//
// It cannot check the property that actually breaks security here: a, b, c must
// be *random*, so a triple reconstructed as a=b=c=1 on every call is a leak
// (the opened d, e are then just x and y).
func debugAnd(alice, bob *Party, n *Node, tA, tB MultShare, aD, bD, aE, bE bool) {
	if !DebugEval {
		return
	}

	a, b, c := tA.u != tB.u, tA.v != tB.v, tA.w != tB.w
	x := alice.shares[n.L.ID] != bob.shares[n.L.ID]
	y := alice.shares[n.R.ID] != bob.shares[n.R.ID]
	d, e := aD != bD, aE != bE

	fmt.Printf("[and ] node %2d  triple(a=%v b=%v c=%v)  d=%v e=%v   shares A(u=%v v=%v w=%v) B(u=%v v=%v w=%v)\n",
		n.ID, a, b, c, d, e, tA.u, tA.v, tA.w, tB.u, tB.v, tB.w)

	if c != (a && b) {
		fmt.Printf("[and ] node %2d  BROKEN TRIPLE: c=%v, want a AND b = %v\n", n.ID, c, a && b)
	}
	if d != (x != a) || e != (y != b) {
		fmt.Printf("[and ] node %2d  BROKEN BLIND: d=%v (want x xor a = %v), e=%v (want y xor b = %v)  [x=%v y=%v]\n",
			n.ID, d, x != a, e, y != b, x, y)
	}
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
