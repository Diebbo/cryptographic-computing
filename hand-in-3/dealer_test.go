package main

import "testing"

// useDealer installs a dealer with a known seed and returns it, so a test can
// pull randomness out of it directly.
func useDealer(seed int64) *Dealer {
	initDealer(seed)
	return dealer
}

// split must be a XOR sharing: the two halves xor back to v, and neither half
// may be predictable from v alone.
func TestSplitReconstructsAndVaries(t *testing.T) {
	alice := NewParty("Alice", true, 1)

	sawTrue, sawFalse := false, false
	for i := 0; i < 100; i++ {
		for _, v := range []bool{false, true} {
			sA, sB := alice.split(v)
			if (sA != sB) != v {
				t.Fatalf("split(%v) = (%v, %v): shares xor to %v", v, sA, sB, sA != sB)
			}
			if sA {
				sawTrue = true
			} else {
				sawFalse = true
			}
		}
	}
	if !sawTrue || !sawFalse {
		t.Errorf("100 splits never produced a %v first share (false=%v, true=%v) — the shares are not masked",
			!sawTrue, sawFalse, sawTrue)
	}
}

// The triple must satisfy the Beaver identity:
// (uA xor uB) AND (vA xor vB) == (wA xor wB).
func TestMultTripleIsValid(t *testing.T) {
	d := useDealer(2)

	for i := 0; i < 100; i++ {
		a, b := d.GiveMultTriple()
		av, bv, cv := a.u != b.u, a.v != b.v, a.w != b.w
		if cv != (av && bv) {
			t.Fatalf("triple %d: reconstructed a=%v b=%v c=%v, but a AND b = %v", i, av, bv, cv, av && bv)
		}
	}
}

// Validity is not enough — a and b must be *random*. A dealer that hands out
// complementary shares makes every triple reconstruct to a = b = c = 1: the
// identity still holds, but the blinds are gone, so the opened d = x xor a and
// e = y xor b are just the operands in the clear.
func TestMultTripleIsRandom(t *testing.T) {
	d := useDealer(3)

	aSeen, bSeen, cSeen := map[bool]int{}, map[bool]int{}, map[bool]int{}
	for i := 0; i < 200; i++ {
		a, b := d.GiveMultTriple()
		aSeen[a.u != b.u]++
		bSeen[a.v != b.v]++
		cSeen[a.w != b.w]++
	}

	if len(aSeen) != 2 {
		t.Errorf("reconstructed a took only one value over 200 triples: %v — the shares are not random, so d = x xor a leaks x", aSeen)
	}
	if len(bSeen) != 2 {
		t.Errorf("reconstructed b took only one value over 200 triples: %v — the shares are not random, so e = y xor b leaks y", bSeen)
	}
	if len(cSeen) != 2 {
		t.Errorf("reconstructed c took only one value over 200 triples: %v", cSeen)
	}
}
