package main

import "fmt"

func main() {
	alice := NewParty("Alice", true, NewDealer(42))
	bob := NewParty("Bob", true, NewDealer(42))
	aliceBits := []*Node{InputANode(0), InputANode(1), InputANode(0)}
	bobBits := []*Node{InputANode(0), InputANode(1), InputANode(0)}

	circuit := BuildCompatibility(aliceBits, bobBits)

	outputA, outputB := EvalNode(alice, bob, circuit)
	fmt.Printf("Alice's share: %v\n", outputA)
	fmt.Printf("Bob's share: %v\n", outputB)
}
