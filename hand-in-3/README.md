# Ex 3 - Implement BeDOZa Passive

Implement using Go.

## Types

```go
typ

```

## Assignment description

Implement a secure two-party protocol for the blood type compatibility function using the passively secure BeDOZa protocol and the Boolean formula from the mandatory assignment of the first note. Since the goal of the exercise is to better understand the protocol (not to build a full functioning system), feel free to implement all parties on the same machine and without using network communication. For example, you could implement the dealer, Alice and Bob as three distinct classes and then let them interact in the following way:
```java
Dealer.Init();
Alice.Init(x,Dealer.RandA());
Bob.Init(y,Dealer.RandB());
while(Alice.hasOutput()==false)
{
Bob.Receive(Alice.Send());
Alice.Receive(Bob.Send());
}
z = Alice.Output();
```
(Note that the loop is not strictly necessary, since you are implementing the protocol for a specific
function so you can predict in advance how many rounds there will be).