package main

import "math/rand"

type Alice struct {
	input   []bool
	pks     []int
	sk      int
	rng     *rand.Rand
	output  bool
	p, q, g int
}

type Bob struct {
	input   int
	pks     []int
	rng     *rand.Rand
	p, q, g int
}

func BoolsToInt(input []bool) int {
	return int(bool[0]) + int(bool[1])*2 + int(bool[2])*4
}

func initAlice(input []bool, seed int64, p, q, g int) *Alice {
	return &Alice{
		input: BoolsToInt(input),
		rng:   rand.New(rand.NewSource(seed)),
		p: p,
		q: q,
		g: g,
	}
}

func (a *Alice) Gen() (int, int) {
	// random sk, retu sk, g^sk
	sk := a.rng.Intn(a.q)
	return sk, a.g ^ sk%a.p
}

func (a *Alice) OGen() int {
	// random sk, retu sk, g^sk
	return (a.rng.Intn(a.p-1) + 1) ^ 2%a.p
}

func (a *Alice) GeneratePks() []int {
	pks := int[]
	// fai mappa/lista di pks, una con Gen per input e salvi sk, per il resto ogen
	// salva la mappa e ritorna
	return [0]
}



func initBob(input []bool, seed int64, p, q, g int) *Bob {
	return &Bob{
		input: input,
		rng:   rand.New(rand.NewSource(seed)),
		p: p,
		q: q,
		g: g,
	}
}
