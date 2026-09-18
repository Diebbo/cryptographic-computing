package main

import "fmt"

func main() {
	initDealer(42)
	alice := NewParty("Alice", true, 57748)
	bob := NewParty("Bob", true, 808)
	aliceShares := []*Node{InputANode(0), InputANode(1), InputANode(2)}
	bobShares := []*Node{InputANode(3), InputANode(4), InputANode(5)}

	aliceBits := []bool{true, true, true}
	bobBits := []bool{false, false, false}

	InitInputs(alice, bob, aliceShares, aliceBits, bobShares, bobBits)

	circuit := BuildCompatibility(aliceShares, bobShares)
	outputID := circuit.ID
	if err := EvalNode(alice, bob, circuit); err != nil {
		panic(err)
	}
	alice.ReceiveOutputShare(outputID, bob.SendOutputShare(outputID))
	outputA := alice.SendOutput(outputID)
	fmt.Printf("Alice's share: %v\n", outputA)
}
