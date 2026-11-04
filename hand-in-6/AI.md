# AI Declaration

I declare that generative AI was used in the preparation of this hand-in as
described below.

**Tool used:** Claude Code (Anthropic).

**How it was used:**

- Reviewed the first draft of `main.py` and listed the bugs and security
  problems in it.
- Fixed the errors that stopped the program from running: the message format
  of `send`/`recv`, gate output wires built from the wrong labels, wire and
  gate counters that were never incremented, gate ids that did not match
  between garbling and evaluation, and the evaluator's lookup of input labels.
- Added the `DEBUG=true` print statements used to trace the circuit.
- Following our instructions, changed the garbling to encrypt
  `label || 0^λ` with a 2λ-bit hash.
- Tested the circuit on all 64 input pairs.
- Wrote this hand-in's `README.md` and this declaration.

**What it was not used for:** The circuit, the input encoding and the
structure of the protocol are our own work and follow the course assignment.
No third-party or online solutions were copied. We reviewed and tested every
AI-assisted change, understand all of the submitted code and take full
responsibility for its content.

Name: Gioele Scandaletti, Diego Barbieri
