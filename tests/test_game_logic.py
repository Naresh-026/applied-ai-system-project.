from logic_utils import check_guess


def test_winning_guess():
    result = check_guess(50, 50)
    assert result == "Win"


def test_guess_too_high():
    result = check_guess(60, 50)
    assert result == "Too High"


def test_guess_too_low():
    result = check_guess(40, 50)
    assert result == "Too Low"
