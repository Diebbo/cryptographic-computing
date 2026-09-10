"""Tests for the one-time truth table protocol in main.py.

Run them with either of:

    python3 -m unittest -v
    python3 -m pytest test_main.py      # if pytest is installed

The protocol draws its randomness from the global ``random`` module, so every
test seeds it first and is therefore fully reproducible.

The suite checks three things:

* the truth table really encodes the blood type rules (against an oracle
  derived independently from the ABO/Rh rules, not from main.py),
* the protocol computes ``table[x][y]`` for all 64 input pairs,
* neither party's input leaks to the other beyond the output bit.
"""

import io
import math
import random
import subprocess
import sys
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

import main

HERE = Path(__file__).resolve().parent

# Seed for every test, so a failure can be reproduced exactly.
SEED = 1234567
# Protocol runs per input used by the uniformity checks.
SAMPLES = 400
# Protocol runs per input pair used by the exhaustive balance check.
PAIR_SAMPLES = 100


# --------------------------------------------------------------------------- #
# oracle and helpers
# --------------------------------------------------------------------------- #


def split_blood_type(blood_type):
    """``'AB+'`` -> ``('AB', True)``; the flag is the presence of the D antigen."""
    abo, sign = blood_type[:-1], blood_type[-1]
    if abo not in ("A", "B", "AB", "O") or sign not in "+-":
        raise ValueError(f"not a blood type: {blood_type!r}")
    return abo, sign == "+"


def can_receive(recipient, donor):
    """Blood compatibility derived from the ABO/Rh rules, independent of main.py."""
    rec_abo, rec_has_d = split_blood_type(recipient)
    don_abo, don_has_d = split_blood_type(donor)
    if don_has_d and not rec_has_d:
        return 0  # a D-negative recipient has (or develops) anti-D antibodies
    if "A" in don_abo and "A" not in rec_abo:
        return 0  # the recipient has anti-A antibodies
    if "B" in don_abo and "B" not in rec_abo:
        return 0  # the recipient has anti-B antibodies
    return 1


# Oracle table, indexed exactly like Dealer.can_receive_table.
EXPECTED_TABLE = [
    [can_receive(recipient, donor) for donor in main.BLOOD_TYPES]
    for recipient in main.BLOOD_TYPES
]


def run_protocol(x, y, seed=SEED):
    """Run one execution of the protocol for Alice's input x and Bob's input y.

    Returns ``(dealer, alice, bob, output_bit)`` so tests can inspect the
    parties' views as well as the result.
    """
    random.seed(seed)
    dealer = main.Dealer()
    alice = main.Alice()
    bob = main.Bob()
    alice.Init(x, dealer.RandA())
    bob.Init(y, dealer.RandB())
    bob.Receive(alice.Send())
    alice.Receive(bob.Send())
    return dealer, alice, bob, alice.Output()


class ProtocolTestCase(unittest.TestCase):
    """Shared assertions."""

    def assert_matrix(self, matrix):
        self.assertEqual(len(matrix), 8)
        for row in matrix:
            self.assertEqual(len(row), 8)
            for entry in row:
                self.assertIn(entry, (0, 1))

    def assert_uniform(self, counter, label="", bins=8):
        """Assert the counted values are spread evenly over ``bins`` buckets."""
        self.assertEqual(sorted(counter), list(range(bins)), f"{label}: missing")
        expected = sum(counter.values()) / bins
        tolerance = 4 * math.sqrt(expected)
        for value, count in sorted(counter.items()):
            self.assertLessEqual(
                abs(count - expected),
                tolerance,
                f"{label}: value {value} seen {count} times, "
                f"expected about {expected:.0f}",
            )


# --------------------------------------------------------------------------- #
# the truth table
# --------------------------------------------------------------------------- #


class TestTruthTable(ProtocolTestCase):
    def setUp(self):
        random.seed(SEED)
        self.table = main.Dealer().can_receive_table

    def test_shape_and_entries_are_bits(self):
        self.assert_matrix(self.table)

    def test_matches_the_abo_rh_rules(self):
        for i, recipient in enumerate(main.BLOOD_TYPES):
            for j, donor in enumerate(main.BLOOD_TYPES):
                with self.subTest(recipient=recipient, donor=donor):
                    self.assertEqual(self.table[i][j], can_receive(recipient, donor))

    def test_row_and_column_order_matches_convert(self):
        self.assertEqual(list(main.BLOOD_TYPES.values()), list(range(8)))
        for name, index in main.BLOOD_TYPES.items():
            with self.subTest(blood_type=name):
                # everyone can receive their own exact blood type
                self.assertEqual(self.table[index][index], 1)

    def test_o_negative_is_the_universal_donor(self):
        o_neg = main.convert("O-")
        # its column is all ones: every recipient can take O- blood
        self.assertEqual([row[o_neg] for row in self.table], [1] * 8)

    def test_ab_positive_is_the_universal_recipient(self):
        ab_pos = main.convert("AB+")
        # its row is all ones: it can receive from every donor
        self.assertEqual(self.table[ab_pos], [1] * 8)

    def test_o_negative_recipient_can_only_take_o_negative(self):
        o_neg = main.convert("O-")
        self.assertEqual(sum(self.table[o_neg]), 1)

    def test_ab_positive_donor_only_fits_ab_positive(self):
        ab_pos = main.convert("AB+")
        self.assertEqual([row[ab_pos] for row in self.table], [0] * 7 + [1])


class TestConvert(unittest.TestCase):
    def test_every_type_maps_to_its_own_index(self):
        self.assertEqual(
            {name: main.convert(name) for name in main.BLOOD_TYPES},
            dict(main.BLOOD_TYPES),
        )
        self.assertEqual(sorted(main.BLOOD_TYPES.values()), list(range(8)))

    def test_is_case_sensitive(self):
        with self.assertRaises(KeyError):
            main.convert("a+")

    def test_unknown_type_raises_key_error(self):
        for bad in ("A++", "C+", "", "AB"):
            with self.subTest(blood_type=bad):
                with self.assertRaises(KeyError):
                    main.convert(bad)


# --------------------------------------------------------------------------- #
# the dealer
# --------------------------------------------------------------------------- #


class TestDealer(ProtocolTestCase):
    def test_shifts_are_row_and_column_indices(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                random.seed(seed)
                dealer = main.Dealer()
                self.assertIn(dealer.r, range(8))
                self.assertIn(dealer.s, range(8))

    def test_rand_a_is_the_shifted_table_masked_with_rand_b(self):
        random.seed(SEED)
        dealer = main.Dealer()
        mat_a, r = dealer.RandA()
        mat_b, s = dealer.RandB()
        self.assert_matrix(mat_a)
        self.assert_matrix(mat_b)
        for i in range(8):
            for j in range(8):
                with self.subTest(i=i, j=j):
                    # Alice's matrix is the real table, shifted by (r, s) and
                    # masked with Bob's matrix.
                    expected = (
                        dealer.can_receive_table[(i - r) % 8][(j - s) % 8]
                        ^ mat_b[i][j]
                    )
                    self.assertEqual(mat_a[i][j], expected)

    def test_rand_b_hands_out_the_mask_and_the_column_shift(self):
        random.seed(SEED)
        dealer = main.Dealer()
        mat_b, s = dealer.RandB()
        self.assertEqual(s, dealer.s)
        self.assertEqual(mat_b, dealer.randomMatrix)

    def test_alice_and_bob_do_not_share_a_matrix_object(self):
        random.seed(SEED)
        dealer = main.Dealer()
        mat_a, _ = dealer.RandA()
        mat_b, _ = dealer.RandB()
        self.assertIsNot(mat_a, mat_b)

    def test_masks_look_random(self):
        random.seed(SEED)
        dealer = main.Dealer()
        mat_b, _ = dealer.RandB()
        ones = sum(sum(row) for row in mat_b)
        # ~32 of 64 entries, generously bounded
        self.assertGreater(ones, 12)
        self.assertLess(ones, 52)

    def test_dealers_differ_between_runs(self):
        rows, shifts = set(), set()
        for seed in range(20):
            random.seed(seed)
            dealer = main.Dealer()
            rows.add(tuple(map(tuple, dealer.randomMatrix)))
            shifts.add((dealer.r, dealer.s))
        self.assertGreater(len(rows), 1)
        self.assertEqual(len({r for r, _ in shifts}), 8)
        self.assertEqual(len({s for _, s in shifts}), 8)

    def test_alice_is_told_r_and_bob_is_told_s(self):
        random.seed(SEED)
        dealer = main.Dealer()
        _, r = dealer.RandA()
        _, s = dealer.RandB()
        self.assertEqual(r, dealer.r)
        self.assertEqual(s, dealer.s)


# --------------------------------------------------------------------------- #
# protocol correctness
# --------------------------------------------------------------------------- #


class TestProtocol(ProtocolTestCase):
    def test_output_is_the_real_table_entry_for_every_pair(self):
        for x_name in main.BLOOD_TYPES:
            for y_name in main.BLOOD_TYPES:
                x, y = main.convert(x_name), main.convert(y_name)
                for seed in range(5):
                    _, _, _, z = run_protocol(x, y, seed)
                    with self.subTest(recipient=x_name, donor=y_name, seed=seed):
                        self.assertEqual(z, EXPECTED_TABLE[x][y])

    def test_output_is_a_single_bit(self):
        for seed in range(50):
            with self.subTest(seed=seed):
                self.assertIn(run_protocol(3, 0, seed)[3], (0, 1))

    def test_alices_output_is_the_masked_entries_xor(self):
        _, alice, bob, z = run_protocol(3, 5)
        # what Alice reads off her own matrix and what Bob sent her
        self.assertEqual(z, alice.zb ^ alice.matA[alice.u][alice.v])

    def test_bobs_reply_is_his_matrix_entry(self):
        _, alice, bob, _ = run_protocol(3, 5)
        self.assertEqual(alice.v, bob.v)
        self.assertEqual(alice.zb, bob.matB[bob.u][bob.v])

    def test_known_pairs(self):
        # A+ recipient, O- donor -> compatible (the default demo run)
        self.assertEqual(run_protocol(main.convert("A+"), main.convert("O-"))[3], 1)
        # A- recipient, B+ donor -> not compatible
        self.assertEqual(run_protocol(main.convert("A-"), main.convert("B+"))[3], 0)
        # AB+ recipient, AB+ donor -> compatible
        self.assertEqual(run_protocol(main.convert("AB+"), main.convert("AB+"))[3], 1)
        # O- recipient, AB+ donor -> not compatible
        self.assertEqual(run_protocol(main.convert("O-"), main.convert("AB+"))[3], 0)

    def test_behaves_the_same_without_extra_randomness(self):
        # a fresh interpreter run must agree with the in-process result
        z = run_protocol(3, 0)[3]
        self.assertEqual(z, EXPECTED_TABLE[3][0])


# --------------------------------------------------------------------------- #
# privacy of the inputs
# --------------------------------------------------------------------------- #


class TestPrivacy(ProtocolTestCase):
    """Each party must learn only what the function output tells them."""

    def test_alice_sees_nothing_about_y_before_bobs_reply(self):
        # With the same dealer randomness, Alice's whole view before Bob's
        # message is identical whatever y is.
        x = main.convert("A+")
        base = None
        for y in range(8):
            _, alice, _, _ = run_protocol(x, y)
            view = (alice.matA, alice.r, alice.u)
            if base is None:
                base = view
            with self.subTest(y=y):
                self.assertEqual(view, base)

    def test_bob_sees_nothing_about_x_in_his_own_setup(self):
        # Bob's matrix, shift and outgoing column index do not depend on x.
        y = main.convert("O-")
        base = None
        for x in range(8):
            _, _, bob, _ = run_protocol(x, y)
            view = (bob.matB, bob.s, bob.v)
            if base is None:
                base = view
            with self.subTest(x=x):
                self.assertEqual(view, base)

    def test_the_row_alice_sends_hides_x_behind_a_uniform_pad(self):
        # u = (r + x) mod 8 with r uniform, so u is uniform for every x.
        for x in range(8):
            counter = Counter(
                run_protocol(x, 0, seed)[1].u for seed in range(SAMPLES)
            )
            with self.subTest(x=x):
                self.assert_uniform(counter, label=f"u for x={x}")

    def test_the_column_bob_sends_hides_y_behind_a_uniform_pad(self):
        # v = (y + s) mod 8 with s uniform, so v is uniform for every y.
        for y in range(8):
            counter = Counter(
                run_protocol(0, y, seed)[2].v for seed in range(SAMPLES)
            )
            with self.subTest(y=y):
                self.assert_uniform(counter, label=f"v for y={y}")

    def test_bobs_reply_bit_is_a_fair_coin_for_every_pair(self):
        # The masked entry Bob sends is independent of the answer it hides.
        for x in range(8):
            for y in range(8):
                counter = Counter(
                    run_protocol(x, y, seed)[1].zb for seed in range(PAIR_SAMPLES)
                )
                with self.subTest(x=x, y=y):
                    self.assert_uniform(counter, label=f"reply bit for {x},{y}", bins=2)

    def test_the_output_bit_still_matches_the_function(self):
        # ...and after all that masking the answer is still correct.
        self.assertEqual(run_protocol(3, 5)[3], EXPECTED_TABLE[3][5])


# --------------------------------------------------------------------------- #
# command line
# --------------------------------------------------------------------------- #


class TestModuleApi(ProtocolTestCase):
    def test_main_runs_with_the_blood_type_names(self):
        random.seed(SEED)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            z = main.main("A+", "O-")
        self.assertEqual(z, EXPECTED_TABLE[main.convert("A+")][main.convert("O-")])
        self.assertIn("compatible", buffer.getvalue())

    def test_main_agrees_with_the_table_for_several_pairs(self):
        for x_name in main.BLOOD_TYPES:
            for y_name in main.BLOOD_TYPES:
                random.seed(SEED)
                with redirect_stdout(io.StringIO()):
                    z = main.main(x_name, y_name)
                with self.subTest(recipient=x_name, donor=y_name):
                    self.assertEqual(
                        z,
                        EXPECTED_TABLE[main.convert(x_name)][main.convert(y_name)],
                    )


class TestCommandLine(ProtocolTestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "main.py", *args],
            cwd=HERE,
            capture_output=True,
            text=True,
        )

    def test_default_run_uses_a_plus_recipient_and_o_minus_donor(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("The two blood types are", result.stdout)
        self.assertIn("compatible", result.stdout)

    def test_arguments_select_the_blood_types(self):
        result = self.run_cli("A-", "B+")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not compatible", result.stdout)

    def test_argument_order_is_recipient_then_donor(self):
        self.assertIn("not compatible", self.run_cli("O-", "AB+").stdout)
        self.assertIn("compatible", self.run_cli("AB+", "O-").stdout)

    def test_unknown_blood_type_is_reported_without_a_traceback(self):
        result = self.run_cli("A+", "C+")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("C+", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_wrong_number_of_arguments_prints_usage(self):
        for args in (("A+",), ("A+", "O-", "B+")):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("usage", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
