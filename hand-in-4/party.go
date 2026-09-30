package main

import "math/rand"

type Party struct {
	Name    string
	IsAlice bool
	shares  map[int]bool
	rng     *rand.Rand
	output  bool
}

func NewParty(name string, isAlice bool, seed int64) *Party {
	return &Party{
		Name:    name,
		IsAlice: isAlice,
		shares:  make(map[int]bool),
		rng:     rand.New(rand.NewSource(seed)),
	}
}

func (p *Party) randBit() bool {
	return p.rng.Intn(2) == 1
}

func (p *Party) Choose() bool {
	return p.rng.Intn(2) == 1
}

func (p *Party) Transfer(y Bool [], pk Int []) bool {
	return p.rng.Intn(2) == 1
}

func (p *Party) Retrieve() bool {
	return p.rng.Intn(2) == 1
}





