package main

import (
	"fmt"
	"testing"
)

// --- test helpers ----------------------------------------------------------

// evalPlain evaluates a node with real values and no secret sharing. This is
// the definition of what each gate means; the two-party EvalNode must agree
// with it.
func evalPlain(n *Node, x, y []bool) bool {
	switch n.Op {
	case InputA:
		return x[n.InputIdx]
	case InputB:
		return y[n.InputIdx]
	case ConstGate:
		return n.ConstVal
	case Xor:
		return evalPlain(n.L, x, y) != evalPlain(n.R, x, y)
	case And:
		return evalPlain(n.L, x, y) && evalPlain(n.R, x, y)
	case XorConst:
		return evalPlain(n.L, x, y) != n.ConstVal
	case AndConst:
		return evalPlain(n.L, x, y) && n.ConstVal
	default:
		panic(fmt.Sprintf("evalPlain: unknown gate %v", n.Op))
	}
}

// walk returns every node reachable from n, including n. Uses a visited set so
// a shared subexpression isn't visited twice.
func walk(n *Node) []*Node {
	var out []*Node
	seen := map[*Node]bool{}
	var rec func(*Node)
	rec = func(n *Node) {
		if n == nil || seen[n] {
			return
		}
		seen[n] = true
		out = append(out, n)
		rec(n.L)
		rec(n.R)
	}
	rec(n)
	return out
}

// buildCompat builds the compatibility circuit over width-bit inputs.
func buildCompat(width int) *Node {
	xs := make([]*Node, width)
	ys := make([]*Node, width)
	for i := range xs {
		xs[i] = InputANode(i)
		ys[i] = InputBNode(i)
	}
	return BuildCompatibility(xs, ys)
}

// --- leaves ----------------------------------------------------------------

func TestConstNode(t *testing.T) {
	for _, v := range []bool{false, true} {
		if got := evalPlain(ConstNode(v), nil, nil); got != v {
			t.Errorf("ConstNode(%v) evaluates to %v", v, got)
		}
	}
}

func TestInputNodesReadTheRightIndex(t *testing.T) {
	x := []bool{true, false, true}
	y := []bool{false, true, true}
	for i := range x {
		if got := evalPlain(InputANode(i), x, y); got != x[i] {
			t.Errorf("InputANode(%d) = %v, want %v", i, got, x[i])
		}
		if got := evalPlain(InputBNode(i), x, y); got != y[i] {
			t.Errorf("InputBNode(%d) = %v, want %v", i, got, y[i])
		}
	}
}

// --- gates -----------------------------------------------------------------

// bb is one row of a binary truth table.
type bb struct{ a, b, want bool }

func TestBinaryGates(t *testing.T) {
	cases := []struct {
		name  string
		build func(l, r *Node) *Node
		table []bb
	}{
		{"Xor", XorGate, []bb{
			{false, false, false},
			{false, true, true},
			{true, false, true},
			{true, true, false},
		}},
		{"And", AndGate, []bb{
			{false, false, false},
			{false, true, false},
			{true, false, false},
			{true, true, true},
		}},
		{"Or", OrGate, []bb{
			{false, false, false},
			{false, true, true},
			{true, false, true},
			{true, true, true},
		}},
		{"OrNot", OrNotGate, []bb{
			{false, false, true},
			{false, true, false},
			{true, false, true},
			{true, true, true},
		}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			for _, row := range c.table {
				n := c.build(ConstNode(row.a), ConstNode(row.b))
				if got := evalPlain(n, nil, nil); got != row.want {
					t.Errorf("%s(%v, %v) = %v, want %v", c.name, row.a, row.b, got, row.want)
				}
			}
		})
	}
}

func TestUnaryGates(t *testing.T) {
	cases := []struct {
		name  string
		build func(*Node) *Node
		want  []bool // indexed by input value
	}{
		{"Not", NotGate, []bool{true, false}},
		{"XorConst(true)", func(a *Node) *Node { return XorConstGate(a, true) }, []bool{true, false}},
		{"XorConst(false)", func(a *Node) *Node { return XorConstGate(a, false) }, []bool{false, true}},
		{"AndConst(true)", func(a *Node) *Node { return AndConstGate(a, true) }, []bool{false, true}},
		{"AndConst(false)", func(a *Node) *Node { return AndConstGate(a, false) }, []bool{false, false}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			for a := 0; a < 2; a++ {
				in := a == 1
				n := c.build(ConstNode(in))
				if got := evalPlain(n, nil, nil); got != c.want[a] {
					t.Errorf("%s(%v) = %v, want %v", c.name, in, got, c.want[a])
				}
			}
		})
	}
}

// --- the whole circuit -----------------------------------------------------

func TestBuildCompatibilityMatchesPlaintext(t *testing.T) {
	const width = 3
	out := buildCompat(width)

	for mask := 0; mask < 1<<(2*width); mask++ {
		x := make([]bool, width)
		y := make([]bool, width)
		for i := 0; i < width; i++ {
			x[i] = mask&(1<<i) != 0
			y[i] = mask&(1<<(width+i)) != 0
		}
		want := plaintextCompat(x, y)
		if got := evalPlain(out, x, y); got != want {
			t.Errorf("compat(x=%v, y=%v) = %v, want %v", x, y, got, want)
		}
	}
}

// --- DAG invariants --------------------------------------------------------

func TestNodeIDsAreUnique(t *testing.T) {
	ResetIDs()
	out := buildCompat(4)

	nodes := walk(out)
	if len(nodes) == 0 {
		t.Fatal("walk found no nodes")
	}

	seen := map[int]*Node{}
	for _, n := range nodes {
		if prev, dup := seen[n.ID]; dup {
			t.Errorf("%v and %v share ID %d", prev.Op, n.Op, n.ID)
		}
		seen[n.ID] = n
	}
}

// The protocol memoises shares in a map keyed by node ID, and main can evaluate
// bottom-up over nodes in creation order instead of recursing. Both rely on
// children being minted before their parents.
func TestChildrenAreCreatedBeforeParents(t *testing.T) {
	ResetIDs()
	out := buildCompat(4)

	for _, n := range walk(out) {
		for _, child := range []*Node{n.L, n.R} {
			if child != nil && child.ID >= n.ID {
				t.Errorf("%v (id %d) has child %v (id %d) minted too late",
					n.Op, n.ID, child.Op, child.ID)
			}
		}
	}
}

func TestBuildCompatibilityRejectsBadInput(t *testing.T) {
	cases := []struct {
		name   string
		xs, ys []*Node
	}{
		{"no inputs", nil, nil},
		{"length mismatch", []*Node{ConstNode(true)}, []*Node{ConstNode(true), ConstNode(false)}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			defer func() {
				if recover() == nil {
					t.Error("BuildCompatibility did not panic")
				}
			}()
			BuildCompatibility(c.xs, c.ys)
		})
	}
}
