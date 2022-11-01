class Calc:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def add(self):
        return self.a + self.b

    def subtract(self):
        return self.a - self.b

    def multiply(self):
        return self.a * self.b

    def divide(self):
        return self.a / self.b


def test_add_01():
    assert Calc(9, 2).add() == 11


def test_add_02():
    assert Calc(-9, 2).add() == -7


def test_subtract_01():
    assert Calc(10, 2).subtract() == 8


def test_subtract_02():
    assert Calc(-10, 2).subtract() == -12


def test_multiply_01():
    assert Calc(8, 2).multiply() == 16


def test_multiply_02():
    assert Calc(-8, 2).multiply() == -16


def test_divide_01():
    assert Calc(7, 2).divide() == 3.5


def test_divide_02():
    assert Calc(-7, 2).divide() == -3.5
