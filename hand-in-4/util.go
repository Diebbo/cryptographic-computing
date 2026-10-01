package main

type Bits struct {
	b1, b2, b3 bool
}

func bitsToIndex(b Bits) int {
	index := 0
	if b.b1 {
		index |= 4
	}
	if b.b2 {
		index |= 2
	}
	if b.b3 {
		index |= 1
	}
	return index
}

func indexToBits(index int) Bits {
	return Bits{
		b1: index&4 != 0,
		b2: index&2 != 0,
		b3: index&1 != 0,
	}
}

func isCompatible(a, b Bits) bool {
	return (a.b1 || !b.b1) && (a.b2 || !b.b2) && (a.b3 || !b.b3)
}
