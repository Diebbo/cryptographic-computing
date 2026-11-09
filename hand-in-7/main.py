from secrets import randbits

_lambda = 128  # security parameter
LAMBDA_BYTES = _lambda // 8  # e.g. 16
ZERO_BYTES = b'\x00' * LAMBDA_BYTES


P_BITS = 2000
Q_BITS = 10**7
R_BITS =  60
n = 2000

def generate_keys():
    p = randbits(P_BITS - 1) << 1 | 1
    y = [p * randbits(Q_BITS) + randbits(R_BITS) for _ in range(n)]
    return (p, y)


class Player:
    def __init__(self, input_bits):
        self.input_bits = input_bits


if __name__ == "__main__":

    z = Alice.eval()


    print("All tests passed!")


