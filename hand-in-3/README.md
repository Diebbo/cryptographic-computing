# Ex 3 - Implement BeDOZa Passive

Implement using Go.

## Types

```go
typ

```

## Assignment description

Implement a secure two-party protocol for the blood type compatibility function using the passively secure BeDOZa protocol and the Boolean formula from the mandatory assignment of the first note. Since the goal of the exercise is to better understand the protocol (not to build a full functioning system), feel free to implement all parties on the same machine and without using network communication. For example, you could implement the dealer, Alice and Bob as three distinct classes and then let them interact in the following way:

```go
main(){
    Dealer.Init();
    Alice.Init(x,Dealer.RandA());
    Bob.Init(y,Dealer.RandB());
    z = dfs(DAG.outputGate());
}


dfs(Node n){

    if n.value != nil: return n.vaulue

    switch(n.operation){
        AND: given (u,n) and (v, n) in C
        // ask the dealer for 3 value of randomness and secretly compute and
        (a1, b1, c1),(a2, b2, c2) = Dealer.giveMult() // ab=c
        A.mult(
        XOR: xor my two shares
        AND/XOR CONST: do it locally

    }
    rBits = Dealer(operationType)
    Bob.Receive(Alice.Send(rBits));
    Alice.Receive(Bob.Send(rBits));
}
```

(Note that the loop is not strictly necessary, since you are implementing the protocol for a specific function so you can predict in advance how many rounds there will be).

## Specs

A and B run on a single. Whenever they'd need some random values they
can ask the dealer.

We use a directed graph to store all of the operations that both the dealer and
the two players will hold. At each operation we'd have the two player
communicating some values, for instance the subrouting "open" wants them to
share some value. Because each of this is deterministic we can encode what they
need to do in the A/Bob.receive().

