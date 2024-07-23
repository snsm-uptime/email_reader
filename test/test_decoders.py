from src.utils.parser import decode_base64, decode_match, decode_quoted_printable, decode


def test_decode_base64():
    encoded_str = "Q29tcHJvYmFudGUgZGUgdHJhbnNhY2Npw7Nu"
    expected = "Comprobante de transacción"
    assert decode_base64(encoded_str) == expected


def test_decode_quoted_printable():
    encoded_str = "Notificaci=C3=B3n_de_transacci=C3=B3n"
    expected = "Notificación_de_transacción"
    assert decode_quoted_printable(encoded_str) == expected


def test_decode_subject_quoted():
    subject_quoted = "=?UTF-8?Q?Notificaci=C3=B3n_de_transacci=C3=B3n?= MXM S PABLO NORTE H\r\n 05-07-2024 - 19:52"
    expected = "Notificación de transacción MXM S PABLO NORTE H 05-07-2024 - 19:52"
    assert decode(subject_quoted) == expected


def test_decode_subject_base64():
    encoded_subject_base64 = "=?UTF-8?B?Q29tcHJvYmFudGUgZGUgdHJhbnNhY2Npw7Nu?="
    expected = "Comprobante de transacción"
    assert decode(encoded_subject_base64) == expected


def test_decode_normal_subject():
    normal_subject = "testing with normal transaccion"
    expected = "testing with normal transaccion"
    assert decode(normal_subject) == expected


def test_decode_match_quoted_printable():
    expected = "Notificación_de_transacción"
    assert decode_match(
        "=?UTF-8?Q?Notificaci=C3=B3n_de_transacci=C3=B3n?=") == expected


def test_decode_match_base64():
    expected = "Comprobante de transacción"
    assert decode_match(
        "=?UTF-8?B?Q29tcHJvYmFudGUgZGUgdHJhbnNhY2Npw7Nu?=") == expected
