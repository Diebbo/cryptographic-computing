# Hand in 2 — One-time truth table for blood type compatibility

**Diego Barbieri au802245 - Gioele Scandaletti au803277**

A two-party protocol in which Alice and Bob each hold a blood type and learn
only whether one can donate to the other — without revealing their own blood
type. The compatibility function is a 8×8 truth table, so it is evaluated with
the **one-time truth table** (oblivious transfer style) construction.

## Requirements

* Python 3.8 or newer — no third-party packages needed.
* To run the tests you only need the standard library (`unittest`). `pytest`
  also works if you happen to have it.

## Running the program

```
python3 main.py [RECIPIENT DONOR]
```

* `RECIPIENT` is **Alice's** private input (the patient who receives blood).
* `DONOR` is **Bob's** private input (the person giving blood).
* With no arguments, the defaults `A+` and `O-` are used.
* Valid blood types: `O-`, `O+`, `A-`, `A+`, `B-`, `B+`, `AB-`, `AB+`.

```console
$ python3 main.py
The two blood types are compatible, i.e. B can donate to A

$ python3 main.py A- B+
The two blood types are not compatible
```

The sentence refers to the two **parties**, not to blood types A and B: "B can
donate to A" means *Bob* (the donor) can give blood to *Alice* (the recipient).

The program exits with status 1 and a message on stderr if a blood type is
misspelled or the wrong number of arguments is given:

```console
$ python3 main.py A+ C+
unknown blood type 'C+'
expected one of: O-, O+, A-, A+, B-, B+, AB-, AB+
```

To use it from Python instead, call `main.main("A+", "O-")`; it prints the
same line and returns the output bit (`1` = compatible).

## Running the tests

```
python3 -m unittest -v          # all tests, verbose
python3 -m unittest             # all tests, quiet
python3 -m unittest test_main.TestPrivacy      # one test class
```

## How the protocol works

The dealer knows the compatibility table `M`, where `M[i][j] = 1` exactly when
recipient `i` can receive blood from donor `j`. It picks a uniform row shift
`r`, a uniform column shift `s`, and a uniform random bit matrix `R`, then
hands out:

* to **Alice**: `A[i][j] = M[(i - r) mod 8][(j - s) mod 8] ⊕ R[i][j]`, plus `r`
* to **Bob**: `R`, plus `s`

`R` is a one-time pad, so Alice sees only noise unless she knows an entry of
`R`, and Bob never sees the table at all.

1. Alice hides her input `x` behind the row shift and sends `u = (r + x) mod 8`.
   Because `r` is uniform, `u` is uniform and tells Bob nothing about `x`.
2. Bob hides his input `y` behind the column shift and sends back
   `v = (y + s) mod 8` together with the single bit `R[u][v]`. Again `v` is
   uniform, so Alice learns nothing about `y`.
3. Alice combines the two — note `(u - r) mod 8 = x` and `(v - s) mod 8 = y`:

   ```
   A[u][v] ⊕ R[u][v]
     = M[(u - r) mod 8][(v - s) mod 8] ⊕ R[u][v] ⊕ R[u][v]
     = M[x][y]
   ```

Bob sends exactly one bit of the mask — the one entry Alice needs — so Alice learns the single table cell `M[x][y]` and nothing else about the table or about `y`. In this implementation only Alice computes the result: after the run, Bob knows neither the answer nor Alice's blood type.

## AI usage declaration
AI (Gemini) has been used only for the purposes of writing this README file and generating the unit testing (not in the file `main.py`).