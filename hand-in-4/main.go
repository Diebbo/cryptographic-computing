package main

import "fmt"

func main() {

	aliceBits := Bits{b1: true, b2: true, b3: true}
	bobBits := Bits{b1: false, b2: false, b3: false}

	pke := initElGamal(1024)
	var lambda int = 128

	alice := initAlice(aliceBits, 57748, pke, lambda)
	bob := initBob(bobBits, 808, pke, lambda)

	alice.GeneratePks()
	bob.ReceivePks(alice.SendPks())

	messages := bob.GenerateMessages()
	alice.ReceiveMessages(messages)

	outputA := alice.GetOutput()
	fmt.Printf("Alice's input: %v\n", aliceBits)
	fmt.Printf("Bob's input: %v\n", bobBits)
	fmt.Printf("Alice's output: %v\n", outputA)
}
