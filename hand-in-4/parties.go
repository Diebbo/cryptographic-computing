package main

import (
	"math/big"
	"math/rand"
)

type Alice struct {
	input  Bits
	pks    [8]*big.Int
	sk     *big.Int
	rng    *rand.Rand
	output bool
	pke    *ElGamal
	lambda int
}

type Bob struct {
	input  Bits
	pks    [8]*big.Int
	rng    *rand.Rand
	pke    *ElGamal
	lambda int
}

func initAlice(input Bits, seed int64, pke *ElGamal, lambda int) *Alice {
	return &Alice{
		input:  input,
		rng:    rand.New(rand.NewSource(seed)),
		pke:    pke,
		lambda: lambda,
	}
}

func (a *Alice) GeneratePks() {
	pks := [8]*big.Int{}
	// fai mappa/lista di pks, una con Gen per input e salvi sk, per il resto ogen
	// salva la mappa e ritorna
	for i := 0; i < 8; i++ {
		if i == bitsToIndex(a.input) {
			r := a.rng.Intn(1 << (1024 + a.lambda))
			sk, pk := a.pke.Gen(big.NewInt(int64(r)))
			pks[i] = pk
			a.sk = sk
		} else {
			r := a.rng.Intn(1 << (1024 + a.lambda))
			pk := a.pke.OGen(big.NewInt(int64(r)))
			pks[i] = pk
		}
	}
	a.pks = pks
}

func (a *Alice) SendPks() [8]*big.Int {
	return a.pks
}

func (a *Alice) ReceiveMessages(messages [8]*Ciphertext) {
	ct := messages[bitsToIndex(a.input)]
	m := a.pke.Decrypt(ct, a.sk)
	a.output = m.Cmp(big.NewInt(1)) == 0
}

func (a *Alice) GetOutput() bool {
	return a.output
}

func initBob(input Bits, seed int64, pke *ElGamal, lambda int) *Bob {
	return &Bob{
		input:  input,
		rng:    rand.New(rand.NewSource(seed)),
		pke:    pke,
		lambda: lambda,
	}
}

func (b *Bob) ReceivePks(pks [8]*big.Int) {
	b.pks = pks
}

func (b *Bob) GenerateMessages() [8]*Ciphertext {
	messages := [8]*Ciphertext{}
	for i := 0; i < 8; i++ {
		var m *big.Int
		r := b.rng.Intn(1 << (1024 + b.lambda))
		if isCompatible(b.input, indexToBits(i)) {
			m = big.NewInt(1)
		} else {
			m = big.NewInt(-1)
		}
		ciphertext := b.pke.Encrypt(b.pks[i], m, big.NewInt(int64(r)))
		messages[i] = ciphertext
	}
	return messages
}
