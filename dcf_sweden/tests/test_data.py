from dcf_sweden import data


def test_convert_to_sek(monkeypatch):
    def fake_fetch_fx_rate(cur_from, to):
        assert cur_from == "USD"
        assert to == "SEK"
        return 10.0

    monkeypatch.setattr(data, "fetch_fx_rate", fake_fetch_fx_rate)
    assert data.convert_to_sek(1.0, "USD") == 10.0
