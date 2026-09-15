package main

// Each input bit is masked with a dealer bit: the owner keeps the mask as
// its share, the other party receives (bit xor mask).
func InitInputs(alice, bob *Party, dealer *Dealer,
	xNodes []*Node, x []bool, yNodes []*Node, y []bool,
) {
	panic("InitInputs: length mismatch")
}

// Walks the DAG once and returns both parties' shares of the node's value.
// Memoised in each party's `shares` map, so shared subexpressions are
// evaluated (and charged a triple) only once.
func EvalNode(alice, bob *Party, n *Node) (shareA, shareB bool) {
	panic("TODO: implement EvalNode")
}

func evalAndGate(alice, bob *Party, n *Node) (bool, bool) {
	panic("TODO: implement evalAndGate")
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
