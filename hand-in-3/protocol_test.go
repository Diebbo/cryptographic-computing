package main

import (
	"maps"
	"os"
	"testing"
)

// Tests for the two-party path: InitInputs, EvalNode and the Beaver step.
// circuit_test.go covers the plaintext side (evalPlain), which never touches
// either party — so nothing here is checked there.
//
// Each test below is written to fail for one reason, so a failing name is
// itself a diagnosis. They run with the per-node trace off; prefix the command
// with BEDOZA_TRACE=1 to see every wire while one of them fails.

// --- helpers ---------------------------------------------------------------

// open reconstructs a shared bit the way the two parties do.
func open(shareA, shareB bool) bool { return shareA != shareB }

// quiet silences the per-node trace for one test (and any subtest using it):
// these tests loop, and a trace per iteration buries the failure.
//
// Set BEDOZA_TRACE to keep the trace on and watch every wire, which is what you
// want when a test is failing and you need to see where the value goes wrong:
//
//	BEDOZA_TRACE=1 go test -run TestGatesThroughTheProtocol -v
func quiet(t *testing.T) {
	t.Helper()
	if os.Getenv("BEDOZA_TRACE") != "" {
		return
	}
	was := DebugEval
	DebugEval = false
	t.Cleanup(func() { DebugEval = was })
}

// mintInputs resets the node counter and the dealer, then returns two empty
// parties plus the input nodes for x and y — with no shares set yet.
func mintInputs(seed int64, x, y []bool) (alice, bob *Party, xs, ys []*Node) {
	ResetIDs()
	initDealer(seed)
	alice, bob = NewParty("Alice", true, 11), NewParty("Bob", false, 22)

	xs = make([]*Node, len(x))
	ys = make([]*Node, len(y))
	for i := range xs {
		xs[i] = InputANode(i)
	}
	for j := range ys {
		ys[j] = InputBNode(j)
	}
	return alice, bob, xs, ys
}

// sharedInputs does the input sharing in the test rather than through
// InitInputs, so that the tests below fail for their own reasons only: with
// InitInputs in the path, a bug there poisons every gate downstream and the
// gate tests stop saying anything about gates. InitInputs has its own test.
func sharedInputs(seed int64, x, y []bool) (alice, bob *Party, xs, ys []*Node) {
	alice, bob, xs, ys = mintInputs(seed, x, y)
	for i, bit := range x {
		a, b := alice.split(bit)
		alice.shares[xs[i].ID] = a
		bob.shares[xs[i].ID] = b
	}
	for j, bit := range y {
		b, a := bob.split(bit)
		alice.shares[ys[j].ID] = a
		bob.shares[ys[j].ID] = b
	}
	return alice, bob, xs, ys
}

// freshProtocol is the whole path: the same setup, but the input shares come
// from InitInputs, exactly as the protocol does it.
func freshProtocol(seed int64, x, y []bool) (alice, bob *Party, xs, ys []*Node) {
	alice, bob, xs, ys = mintInputs(seed, x, y)
	InitInputs(alice, bob, xs, x, ys, y)
	return alice, bob, xs, ys
}

// evalTwoParty runs the protocol on one node and returns the reconstructed
// output bit.
func evalTwoParty(t *testing.T, alice, bob *Party, n *Node) bool {
	t.Helper()
	if err := EvalNode(alice, bob, n); err != nil {
		t.Fatalf("EvalNode: %v", err)
	}
	return open(alice.shares[n.ID], bob.shares[n.ID])
}

// runGate evaluates one gate over one input bit per party, with the inputs
// shared correctly so a failure points at the gate itself.
func runGate(t *testing.T, x, y bool, build func(xn, yn *Node) *Node) bool {
	t.Helper()
	alice, bob, xs, ys := sharedInputs(7, []bool{x}, []bool{y})
	return evalTwoParty(t, alice, bob, build(xs[0], ys[0]))
}

// --- input sharing ---------------------------------------------------------

// Every input node must end up with a share in *both* maps, keyed by its own
// ID, and the two shares must xor back to the bit.
//
// Checking that the key exists is the point: a missing key reads back as false,
// so a wire that was never shared is indistinguishable from one carrying 0.
func TestInitInputsSharesEveryInput(t *testing.T) {
	quiet(t)
	x := []bool{true, false, true}
	y := []bool{false, true, true}
	alice, bob, xs, ys := freshProtocol(10, x, y)

	for i, n := range xs {
		a, okA := alice.shares[n.ID]
		b, okB := bob.shares[n.ID]
		switch {
		case !okA || !okB:
			t.Errorf("x[%d] (node %d): no share — Alice set=%v, Bob set=%v", i, n.ID, okA, okB)
		case open(a, b) != x[i]:
			t.Errorf("x[%d] (node %d): shares xor to %v, want %v", i, n.ID, open(a, b), x[i])
		}
	}

	for j, n := range ys {
		a, okA := alice.shares[n.ID]
		b, okB := bob.shares[n.ID]
		switch {
		case !okA || !okB:
			t.Errorf("y[%d] (node %d): no share — Alice set=%v, Bob set=%v", j, n.ID, okA, okB)
		case open(a, b) != y[j]:
			t.Errorf("y[%d] (node %d): shares xor to %v, want %v", j, n.ID, open(a, b), y[j])
		}
	}
}

// --- single gates through the protocol -------------------------------------

// A public constant still has to be *shared*: the invariant is
// shareA xor shareB == value, and giving both parties the value reconstructs to
// 0 every time the constant is true. (XorConst avoids this by handing the
// constant to Alice alone — see TestGatesThroughTheProtocol.)
func TestConstGateIsShared(t *testing.T) {
	quiet(t)
	for _, v := range []bool{false, true} {
		initDealer(11)
		alice, bob := NewParty("Alice", true, 11), NewParty("Bob", false, 22)
		n := ConstNode(v)
		if err := EvalNode(alice, bob, n); err != nil {
			t.Fatalf("ConstNode(%v): EvalNode: %v", v, err)
		}
		a, b := alice.shares[n.ID], bob.shares[n.ID]
		if a == b == v {
			t.Errorf("ConstNode(%v): shares A=%v B=%v xor to %v, want %v", v, a, b, open(a, b), v)
		}
	}
}

func TestGatesThroughTheProtocol(t *testing.T) {
	cases := []struct {
		name  string
		build func(xn, yn *Node) *Node
		want  func(x, y bool) bool
	}{
		{"Xor", XorGate, func(x, y bool) bool { return x != y }},
		{"And", AndGate, func(x, y bool) bool { return x && y }},
		{"OrNot", OrNotGate, func(x, y bool) bool { return x || !y }},
		{"Not", func(xn, _ *Node) *Node { return NotGate(xn) }, func(x, _ bool) bool { return !x }},
		{"XorConst(true)", func(xn, _ *Node) *Node { return XorConstGate(xn, true) }, func(x, _ bool) bool { return x != true }},
		{"XorConst(false)", func(xn, _ *Node) *Node { return XorConstGate(xn, false) }, func(x, _ bool) bool { return x != false }},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			quiet(t)
			for _, x := range []bool{false, true} {
				for _, y := range []bool{false, true} {
					got, want := runGate(t, x, y, c.build), c.want(x, y)
					if got != want {
						t.Errorf("%s(x=%v, y=%v): shares reconstruct to %v, want %v", c.name, x, y, got, want)
					}
				}
			}
		})
	}
}

// AndConst is listed in SPECS.md and Party has the method, but EvalNode's
// switch has no case for it — this test says so directly rather than leaving it
// to be discovered when a circuit that uses it fails to evaluate.
func TestAndConstThroughTheProtocol(t *testing.T) {
	quiet(t)
	for _, c := range []bool{false, true} {
		for _, x := range []bool{false, true} {
			alice, bob, xs, _ := sharedInputs(12, []bool{x}, nil)
			n := AndConstGate(xs[0], c)
			got, err := func() (bool, error) {
				if err := EvalNode(alice, bob, n); err != nil {
					return false, err
				}
				return open(alice.shares[n.ID], bob.shares[n.ID]), nil
			}()
			if err != nil {
				t.Fatalf("AndConst(x=%v, c=%v): EvalNode: %v", x, c, err)
			}
			if want := x && c; got != want {
				t.Errorf("AndConst(x=%v, c=%v) = %v, want %v", x, c, got, want)
			}
		}
	}
}

// --- the Beaver step on its own --------------------------------------------

// TestBeaverMultiplicationReconstructs isolates the one interactive step from
// everything else. It hands the parties a triple this test builds itself, so a
// valid dealer is assumed: a failure here points at PrepareMult/FinishMult
// rather than at the dealer or the circuit.
//
// The call convention mirrors evalAndGate — each party blinds with its own
// operand shares and is given the *other* party's d/e. If FinishMult grows the
// addCrossTerm argument from SPECS.md, this is the spot to update (true for
// Alice, false for Bob).
func TestBeaverMultiplicationReconstructs(t *testing.T) {
	quiet(t)
	alice, bob := NewParty("Alice", true, 99), NewParty("Bob", false, 100)

	for _, x := range []bool{false, true} {
		for _, y := range []bool{false, true} {
			for trial := 0; trial < 20; trial++ {
				xA, xB := alice.split(x)
				yA, yB := bob.split(y)

				// a properly random triple: u and v are random, w = u AND v
				uA, uB := alice.split(alice.randBit())
				vA, vB := alice.split(alice.randBit())
				wA, wB := alice.split((uA != uB) && (vA != vB))

				tA := MultShare{u: uA, v: vA, w: wA}
				tB := MultShare{u: uB, v: vB, w: wB}

				dA, eA := alice.PrepareMult(tA, xA, yA)
				dB, eB := bob.PrepareMult(tB, xB, yB)

				d := dA != dB
				e := eA != eB

				zA := alice.FinishMult(tA, d, e, xA, yA)
				zB := bob.FinishMult(tB, d, e, xB, yB)

				if got, want := open(zA, zB), x && y; got != want {
					t.Fatalf("x=%v y=%v trial %d: shares reconstruct to %v, want %v (d=%v e=%v)",
						x, y, trial, got, want, dA != dB, eA != eB)
				}
			}
		}
	}
}

// --- whole circuits --------------------------------------------------------

// The target function over all 64 input combinations, compared against the
// plaintext definition. Every case gets a fresh dealer, so a failure is
// reproducible from the seed printed with it.
func TestCompatibilityMatchesPlaintext(t *testing.T) {
	quiet(t)
	const width = 3

	for mask := 0; mask < 1<<(2*width); mask++ {
		x := make([]bool, width)
		y := make([]bool, width)
		for i := 0; i < width; i++ {
			x[i] = mask&(1<<i) != 0
			y[i] = mask&(1<<(width+i)) != 0
		}

		alice, bob, xs, ys := freshProtocol(int64(mask)+1, x, y)
		out := BuildCompatibility(xs, ys)

		got, want := evalTwoParty(t, alice, bob, out), plaintextCompat(x, y)
		if got != want {
			t.Errorf("compat(x=%v, y=%v) = %v, want %v (seed %d)", x, y, got, want, mask+1)
		}
	}
}

// main.go's scenario, end to end, including the opening path it uses: every bit
// is true on both sides, so every OrNot is true and the compatibility function
// answers true.
func TestEndToEndOutputOpening(t *testing.T) {
	quiet(t)
	x := []bool{true, true, true}
	y := []bool{true, true, true}

	alice, bob, xs, ys := freshProtocol(42, x, y)
	out := BuildCompatibility(xs, ys)

	if got := evalTwoParty(t, alice, bob, out); got != true {
		t.Errorf("compat(%v, %v) = %v, want true", x, y, got)
	}

	// The same exchange main.go does. ReceiveOutputShare folds Bob's share into
	// Alice's map, so it must run after the checks above and only once.
	alice.ReceiveOutputShare(out.ID, bob.SendOutputShare(out.ID))
	if got := alice.SendOutput(out.ID); got != true {
		t.Errorf("after opening, Alice holds %v, want true", got)
	}
}

// EvalNode's comment promises a shared subexpression is evaluated once. That is
// not cosmetic: every evaluation of an And node burns a fresh triple, so a node
// with two parents would be charged twice, and its two shares would change
// under it after the first parent already used them.
//
// Detected by evaluating twice and requiring nothing moved — a re-evaluation
// that hits a memoised node is a no-op. Several seeds, because a fresh triple
// could in principle reproduce the old shares by chance.
func TestReEvaluatingIsANoOp(t *testing.T) {
	quiet(t)

	for seed := int64(0); seed < 8; seed++ {
		alice, bob, xs, ys := freshProtocol(seed, []bool{true, false}, []bool{false, true})

		shared := AndGate(xs[0], ys[0]) // two parents, so EvalNode reaches it twice
		out := XorGate(shared, AndGate(shared, ys[1]))

		if err := EvalNode(alice, bob, out); err != nil {
			t.Fatalf("seed %d: EvalNode: %v", seed, err)
		}
		wantA, wantB := maps.Clone(alice.shares), maps.Clone(bob.shares)

		if err := EvalNode(alice, bob, out); err != nil {
			t.Fatalf("seed %d: second EvalNode: %v", seed, err)
		}

		for id, want := range wantA {
			if got := alice.shares[id]; got != want {
				t.Errorf("seed %d: re-evaluating changed Alice's share of node %d from %v to %v", seed, id, want, got)
			}
		}
		for id, want := range wantB {
			if got := bob.shares[id]; got != want {
				t.Errorf("seed %d: re-evaluating changed Bob's share of node %d from %v to %v", seed, id, want, got)
			}
		}
	}
}
