# Ex 3 - Implement BeDOZa Passive

A Go implementation of a passively-secure two-party computation (2PC) protocol using XOR-sharing and Beaver triples for secure AND multiplication. Parties compute a target function over secret inputs without revealing individual bits to each other.

## Overview

This project implements a simplified but cryptographically sound MPC protocol where:

- **Alice** and **Bob** each hold a secret bit vector (inputs)
- They jointly compute a **compatibility** function: `CompatibilityCheck(x, y) = AND_i (x_i OR ¬y_i)`
- Neither party learns the other's inputs; only the final result is revealed
- The protocol uses **XOR-sharing** for bit-wise secrets and **Beaver triples** for secure AND gates

The compatibility function checks whether Alice's and Bob's inputs are "compatible" — formally, there is no position where Alice's bit is 0 and Bob's is 1. This is useful for privacy-preserving pattern matching and access control scenarios.

## Protocol Design

### Circuit Model

The computation is expressed as a DAG of gates:

- **Leaves**: input bits (InputA, InputB) and public constants (ConstGate)
- **Operations**:
  - `Xor`, `XorConst` — local computation, no communication
  - `And` — requires one Beaver triple and one opening round
  - Derived: `Not`, `Or`, `OrNot`, `AndConst` — built from primitives

### XOR-Sharing

Every wire in the circuit is represented as a pair of shares held by the two parties. The actual value is the XOR of the shares:

```
value = share_A ⊕ share_B
```

**Critical invariant**: Every secret (including public constants and Beaver triple components) must appear an **odd number of times** across the two parties' representations — typically exactly once per value.

### Beaver Triple Multiplication

Secure AND computation uses the Beaver triple protocol:

1. **Dealer phase** (offline): Generate random $(u, v, w)$ with $w = u \land v$, XOR-share between parties
2. **Preparation** (online, local): Compute $d = x \oplus u$ and $e = y \oplus v$
3. **Opening** (online, interactive): Reveal $d$ and $e$ to both parties
4. **Finalization** (online, local): Each party computes their share of $z = x \land y$ using:

$$z = w \oplus (e \land x) \oplus (d \land y) \oplus (d \land e)$$

where the cross-term $(d \land e)$ is folded into **exactly one party's share** (Alice's) to preserve the parity invariant.

## Architecture

### Files

| File               | Purpose                                                           |
| ------------------ | ----------------------------------------------------------------- |
| `circuit.go`       | Gate definitions, node structure, circuit builders                |
| `party.go`         | Party state, local share operations (Xor, And, FinishMult, etc.)  |
| `dealer.go`        | Beaver triple generation and input masking distribution           |
| `eval.go`          | Circuit evaluation engine; debugging/tracing infrastructure       |
| `main.go`          | Example: all-bits-true scenario                                   |
| `protocol_test.go` | Comprehensive test suite covering all gates and the full protocol |

### Key Types

```go
type GateType int          // Enum: InputA, InputB, ConstGate, Xor, And, ...

type Node struct {         // Immutable circuit node (DAG edge)
    ID       int           // Unique identifier (creation order)
    Op       GateType      // Operation at this node
    ConstVal bool          // For ConstGate, XorConst, AndConst
    L, R     *Node         // Children (nil for leaves)
}

type Party struct {        // One participant
    Name     string
    IsAlice  bool
    shares   map[int]bool  // Wire shares, memoized by node ID
    rng      *rand.Rand    // For input masking
    output   bool          // Final reconstructed output
}

type MultShare struct {    // One party's Beaver triple share
    u, v, w bool
}
```

## Usage

### Building and Testing

```bash
go build ./...
go test ./...
```

Run tests with full per-wire tracing:

```bash
BEDOZA_TRACE=1 go test -run TestCompatibilityMatchesPlaintext -v
```
