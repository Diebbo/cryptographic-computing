# Ex 3 - Implement BeDOZa Passive

Implement using Go.

## Types

### Circuit (DAG)

The circuit is a DAG of gates. Every wire carries one secret bit, XOR-shared
between Alice and Bob (`shareA xor shareB == value`). Nodes describe
_structure only_ — the shares themselves live in each party's private state.

```go
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
	ConstVal bool // ConstGate / XorConst / AndConst
	InputIdx int  // InputA / InputB — for debugging only
    L, R *Node // nil for leaf, R is unused in binary operations
    // remember the root is the output
}

type Grah struct {
    Output *Node
    Nodes  []*Node
}
```

Constructors for the primitive gates:

```go
func InputANode(idx int) *Node
func InputBNode(idx int) *Node
func ConstNode(v bool) *Node

func XorGate(l, r *Node) *Node
func AndGate(l, r *Node) *Node
func XorConstGate(l *Node, c bool) *Node
func AndConstGate(l *Node, c bool) *Node
```

Derived gates, built from the primitives above:

```go
// NotGate(a)   = a xor 1
// OrGate(a,b)  = (a xor b) xor (a and b)
// OrNotGate(x,y) = x or not y
//               = (x xor y xor 1) xor (x and (y xor 1))
func NotGate(a *Node) *Node
func OrGate(a, b *Node) *Node
func OrNotGate(x, y *Node) *Node

// Target function: AND over all bit positions of OrNot(x_i, y_i).
func BuildCompatibility(xs, ys []*Node) *Node
```

### Dealer

Trusted (we only need passive security). Hands out:

- one XOR mask per input bit, used to secret-share inputs;
- one Beaver triple `(a, b, c)` with `c = a AND b` per AND gate, itself
  XOR-shared between the two parties.

```go
// One party's share of a triple. The two parties' shares satisfy
// (aA xor aB) AND (bA xor bB) == (cA xor cB).
type MultShare struct {
	A, B, C bool
}

type Dealer struct {
	rng *rand.Rand
}

func NewDealer(seed int64) *Dealer

func (d *Dealer) randBit() bool
func (d *Dealer) split(v bool) (sA, sB bool) // sA xor sB == v

func (d *Dealer) GiveInputMask() bool
func (d *Dealer) GiveMultTriple() (alice, bob MultShare) // one per AND gate
```

### Party

```go
type Party struct {
	Name    string
	IsAlice bool
	dealer  *Dealer
	shares  map[int]bool // nodeID -> this party's XOR-share of that wire
}

func NewParty(name string, isAlice bool, dealer *Dealer) *Party

// Phase 1 of Beaver multiplication — purely local. Each party blinds its
// shares of x and y with its own share of the triple. The resulting
// (d, e) must be exchanged with the other party before phase 2.
func (p *Party) PrepareMult(t MultShare, xShare, yShare bool) (d, e bool)

// Phase 2 — purely local, once d and e are opened. Exactly one of the two
// parties (by convention Alice) sets addCrossTerm, otherwise the d*e term
// is counted twice.
func (p *Party) FinishMult(t MultShare, d, e bool, addCrossTerm bool) bool
```

### Input sharing and evaluation

```go
// Each input bit is masked with a dealer bit: the owner keeps the mask as
// its share, the other party receives (bit xor mask).
func InitInputs(alice, bob *Party, dealer *Dealer,
	xNodes []*Node, x []bool, yNodes []*Node, y []bool)

// Walks the DAG once and returns both parties' shares of the node's value.
// Memoised in each party's `shares` map, so shared subexpressions are
// evaluated (and charged a triple) only once.
func EvalNode(alice, bob *Party, n *Node) (shareA, shareB bool)

// The only gate requiring interaction.
func evalAndGate(alice, bob *Party, n *Node) (bool, bool)

// Plaintext reference, for testing the circuit against ground truth.
func plaintextCompat(x, y []bool) bool
```

## Assignment description

Implement a secure two-party protocol for the blood type compatibility
function using the passively secure BeDOZa protocol and the Boolean formula
from the mandatory assignment of the first note. Since the goal of the
exercise is to better understand the protocol (not to build a full
functioning system), feel free to implement all parties on the same machine
and without using network communication. For example, you could implement
the dealer, Alice and Bob as three distinct classes and then let them
interact in the following way:

```go
main(){
    Dealer.Init();
    Alice.Init(x,Dealer.RandA());
    Bob.Init(y,Dealer.RandB());
    z = dfs(DAG.outputGate());
}


dfs(Node n){

    if n.value != nil: return n.value

    switch(n.operation){
        AND: given (u,n) and (v, n) in C
        // ask the dealer for 3 value of randomness and secretly compute and
        (a1, b1, c1),(a2, b2, c2) = Dealer.giveMult() // ab=c
        d_A, e_A = A.prepareMult((a1, b1, c1), u, v, n) // computes d_A, e_A and shares d_A
        d_B, e_B = B.prepareMult((a2, b2, c2), u, v, n)
        A.mult((a1, b1, c1), u,v,n, e_B, d_B)
        B.mult((a2, b2, c2), u,v,n, e_A, d_A)
        XOR: xor my two shares locally
        AND CONST: do it locally
        XOR CONST: Alice does it locally, Bob does nothing

    }
}
```

(Note that the loop is not strictly necessary, since you are implementing
the protocol for a specific function so you can predict in advance how many
rounds there will be.)

## Specs

A and B run on a single machine. Whenever they'd need some random values
they can ask the dealer.

We use a directed graph to store all of the operations that both the dealer
and the two players will hold. At each operation we'd have the two players
communicating some values, for instance the subroutine "open" wants them to
share some value. Because each of these is deterministic we can encode what
they need to do in the `Alice/Bob.receive()`.

## Target function

```
f(x,y) = x or not y  -->  (x_1 or not y_1) and (x_2 or not y_2) and ...

not a  = a xor 1
a or b = (a xor b) xor (a and b)

(x_1 or not y_1) = (x_1 xor y_1 xor 1) xor (x_1 and (y_1 xor 1))
```

Only the `and` in that expansion costs a round; everything else is local.