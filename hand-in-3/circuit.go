package main

import "fmt"

// GateType identifies the operation performed at a circuit node.
type GateType int

const (
	InputA    GateType = iota // Alice's input bit
	InputB                    // Bob's input bit
	ConstGate                 // public constant
	Xor                       // x xor y           - local, no communication
	And                       // x and y           - needs a triple + 1 round
	XorConst                  // x xor c, c public - local, only one party applies c
	AndConst                  // x and c, c public - local, AND distributes over XOR
)

func (g GateType) String() string {
	switch g {
	case InputA:
		return "InputA"
	case InputB:
		return "InputB"
	case ConstGate:
		return "ConstGate"
	case Xor:
		return "Xor"
	case And:
		return "And"
	case XorConst:
		return "XorConst"
	case AndConst:
		return "AndConst"
	default:
		return fmt.Sprintf("GateType(%d)", int(g))
	}
}

// Node is one gate in the circuit DAG. The child pointers are the edges: a leaf
// (InputA, InputB, ConstGate) has L and R both nil, the unary const gates use
// only L. Nodes are immutable once built, which is what keeps the graph acyclic.
type Node struct {
	ID       int
	Op       GateType
	ConstVal bool  // ConstGate / XorConst / AndConst
	InputIdx int   // InputA / InputB, for debugging only
	L, R     *Node // nil for leaves; R unused by unary gates
}

// nextID is the circuit-wide node counter. Constructors take already-built
// children, so a parent is always minted after its children: creation order is
// a topological order.
var nextID int

func mint(op GateType) *Node {
	n := &Node{ID: nextID, Op: op}
	nextID++
	return n
}

// ResetIDs restarts the ID counter at zero. Tests call this so they don't
// depend on how many nodes earlier tests built.
func ResetIDs() { nextID = 0 }

// --- primitive gates

func InputANode(idx int) *Node {
	n := mint(InputA)
	n.InputIdx = idx
	return n
}

func InputBNode(idx int) *Node {
	n := mint(InputB)
	n.InputIdx = idx
	return n
}

func ConstNode(v bool) *Node {
	n := mint(ConstGate)
	n.ConstVal = v
	return n
}

func XorGate(l, r *Node) *Node {
	n := mint(Xor)
	n.L, n.R = l, r
	return n
}

func AndGate(l, r *Node) *Node {
	n := mint(And)
	n.L, n.R = l, r
	return n
}

func XorConstGate(l *Node, c bool) *Node {
	n := mint(XorConst)
	n.L, n.ConstVal = l, c
	return n
}

func AndConstGate(l *Node, c bool) *Node {
	n := mint(AndConst)
	n.L, n.ConstVal = l, c
	return n
}

// --- derived gates ---------------------------------------------------------

// NotGate(a) = a xor 1
func NotGate(a *Node) *Node {
	return XorConstGate(a, true)
}

// OrGate(a,b) = (a xor b) xor (a and b)
func OrGate(a, b *Node) *Node {
	return XorGate(XorGate(a, b), AndGate(a, b))
}

// OrNotGate(x,y) = x or not y
//
//	= (x xor y xor 1) xor (x and (y xor 1))
func OrNotGate(x, y *Node) *Node {
	notY := XorConstGate(y, true)
	return OrGate(x, notY)
}

// BuildCompatibility wires up the target function: the AND over all bit
// positions of OrNot(x_i, y_i). Panics on a bad call, since a length mismatch
// or an empty input is a programming error, not a runtime condition.
func BuildCompatibility(xs, ys []*Node) *Node {
	if len(xs) != len(ys) {
		panic(fmt.Sprintf("BuildCompatibility: %d x-nodes, %d y-nodes", len(xs), len(ys)))
	}
	if len(xs) == 0 {
		panic("BuildCompatibility: no input bits")
	}
	out := OrNotGate(xs[0], ys[0])
	for i := 1; i < len(xs); i++ {
		out = AndGate(out, OrNotGate(xs[i], ys[i]))
	}
	return out
}
