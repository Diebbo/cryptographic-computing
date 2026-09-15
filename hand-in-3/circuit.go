package main

type GateType int

const (
	InputA    GateType = iota // Alice's input bit
	InputB                    // Bob's input bit
	ConstGate                 // public constant
	Xor                       // x xor y            — local, no communication
	And                       // x and y            — needs a triple + 1 round
	XorConst                  // x xor c, c public  — local, only one party applies c
	AndConst                  // x and c, c public  — local, AND distributes over XOR
)

type Node struct {
	ID       int
	Op       GateType
	ConstVal bool  // ConstGate / XorConst / AndConst
	InputIdx int   // InputA / InputB — for debugging only
	L, R     *Node // nil for leafs, R is unused in binary operations
}

type Grah struct {
	Output *Node
	Nodes  []*Node
}

// Alice's Graphs and bob's one

func InputANode(idx int) *Node {
	// Create a new input node for Alice's input bit at index idx
	return &Node{
		ID:       idx,
		Op:       InputA,
		InputIdx: idx,
	}
}

func InputBNode(idx int) *Node {
	return &Node{
		ID:       idx,
		Op:       InputB,
		InputIdx: idx,
	}
}

func ConstNode(v bool) *Node {
	return &Node{
		ID:       -1, // ID is not relevant for constants
		Op:       ConstGate,
		ConstVal: v,
	}
}

func XorGate(l, r *Node) *Node {
	return &Node{
		ID:       -1, // ID is not relevant for internal nodes
		Op:       Xor,
		L:        l,
		R:        r,
		ConstVal: false, // Not used for Xor gate
	}
}

func AndGate(l, r *Node) *Node {
	return &Node{
		ID:       -1, // ID is not relevant for internal nodes
		Op:       And,
		L:        l,
		R:        r,
		ConstVal: false, // Not used for Xor gate
	}
}

func XorConstGate(l *Node, c bool) *Node {
	return &Node{
		ID:       -1, // ID is not relevant for internal nodes
		Op:       XorConst,
		L:        l,
		ConstVal: c,
	}
}

func AndConstGate(l *Node, c bool) *Node {
	return &Node{
		ID:       -1, // ID is not relevant for internal nodes
		Op:       AndConst,
		L:        l,
		ConstVal: c,
	}
}

// NotGate(a)   = a xor 1
// OrGate(a,b)  = (a xor b) xor (a and b)
// OrNotGate(x,y) = x or not y
//
//	= (x xor y xor 1) xor (x and (y xor 1))
func NotGate(a *Node) *Node {
	return XorConstGate(a, true)
}

func OrGate(a, b *Node) *Node {
	return XorGate(XorGate(a, b), AndGate(a, b))
}

func OrNotGate(x, y *Node) *Node {
	return OrGate(x, NotGate(y))
}

// Target function: AND over all bit positions of OrNot(x_i, y_i).
func BuildCompatibility(xs, ys []*Node) *Node {
	if len(xs) != len(ys) {
		return nil // or handle error
	}

	var result *Node = ConstNode(true) // Start with true (identity for AND)
	for i := 0; i < len(xs); i++ {
		x := xs[i]
		y := ys[i]
		compat := OrNotGate(x, y)
		result = AndGate(result, compat)
	}
	return result
}
