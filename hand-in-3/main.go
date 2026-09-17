package main

import "fmt"

func main() {
	initDealer(42)
	alice := NewParty("Alice", true)
	bob := NewParty("Bob", true)
	aliceShares := []*Node{InputANode(0), InputANode(1), InputANode(2)}
	bobShares := []*Node{InputANode(3), InputANode(4), InputANode(5)}

	aliceBits := []bool{true, false, true}
	bobBits := []bool{false, true, false}

	InitInputs(alice, bob, aliceShares, aliceBits, bobShares, bobBits)

	circuit := BuildCompatibility(aliceShares, bobShares)
	outputID := circuit.ID
	EvalNode(alice, bob, circuit)
	alice.ReceiveOutputShare(outputID, bob.SendOutputShare(outputID))
	outputA := alice.SendOutput(outputID)
	fmt.Printf("Alice's share: %v\n", outputA)
}
