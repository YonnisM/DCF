from dcf_sweden import data


def test_convert_to_sek(monkeypatch):
    def fake_fetch_fx_rate(cur_from, to):
        assert cur_from == "USD"
        assert to == "SEK"
        return 10.0

    monkeypatch.setattr(data, "fetch_fx_rate", fake_fetch_fx_rate)
    assert data.convert_to_sek(1.0, "USD") == 10.0


def test_fetch_market_data(monkeypatch):
    class FakeTicker:
        def __init__(self, ticker):
            assert ticker == "ABC"
            self.info = {
                "regularMarketPrice": 123.0,
                "currency": "USD",
                "sharesOutstanding": 1000,
                "marketCap": 123000,
            }

    monkeypatch.setattr(data, "yf", type("YF", (), {"Ticker": FakeTicker}))
    md = data.fetch_market_data("ABC")
    assert md.price == 123.0
    assert md.currency == "USD"
    assert md.shares_outstanding == 1000
    assert md.market_cap == 123000
