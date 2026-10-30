from uzwatermu.services.accounts import clean_account, normalize_uz_phone, phone_matches


def test_clean_account_keeps_digits():
    assert clean_account(" 10-00 01 ") == "100001"


def test_normalize_phone():
    assert normalize_uz_phone("+998 90 123 45 67") == "998901234567"
    assert normalize_uz_phone("901234567") == "998901234567"
    assert normalize_uz_phone("12345") is None


def test_phone_matches():
    assert phone_matches("90 123 45 67", "+998901234567")
    assert not phone_matches("90 123 45 67", "+998911234567")
    assert not phone_matches("", "")
