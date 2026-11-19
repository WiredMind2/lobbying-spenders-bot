"""Tests for name normalization and client->ticker matching (no network)."""

from lobbying_bot.edgar import ClientMapper, TickerMap, normalize_name


def test_normalize_strips_punctuation_and_suffixes():
    # "COM" is not a legal suffix, so it survives normalization
    assert normalize_name("Amazon.com Services LLC") == "AMAZON COM SERVICES"
    assert normalize_name("Meta Platforms, Inc.") == "META PLATFORMS"
    assert normalize_name("  Northrop Grumman Corp. ") == "NORTHROP GRUMMAN"


def test_normalize_keeps_distinctive_words():
    assert normalize_name("United Therapeutics Corporation") == "UNITED THERAPEUTICS"


def _mapper(edgar_titles):
    payload = {str(i): {"cik_str": 1, "ticker": t, "title": title}
               for i, (t, title) in enumerate(edgar_titles)}
    return ClientMapper(TickerMap.from_edgar(payload), overrides={})


def test_match_exact_after_normalization():
    mapper = _mapper([("AMZN", "Amazon.com, Inc."), ("UTX", "United Technologies")])
    ticker, method = mapper.match("Amazon.com Inc")
    assert (ticker, method) == ("AMZN", "exact")


def test_match_exact_via_suffix_normalization():
    # "Corporation" and "Corp" normalize the same way -> exact, no fuzzy needed
    mapper = _mapper([("UTR", "United Therapeutics Corp")])
    assert mapper.match("United Therapeutics Corporation") == ("UTR", "exact")


def test_match_fuzzy_tight_cutoff():
    # truncated variant that survives normalization must still match fuzzily
    mapper = _mapper([("NOC", "Northrop Grumman Systems Corporation")])
    ticker, method = mapper.match("Northrop Grumman Syst")
    assert (ticker, method) == ("NOC", "fuzzy")


def test_match_unmapped_for_unlikely_names():
    mapper = _mapper([("AMZN", "Amazon.com, Inc.")])
    assert mapper.match("AMERICAN FAMILIES FOR FAIRNESS") == (None, "none")


def test_override_beats_edgar():
    mapper = ClientMapper(
        TickerMap(by_name={"ALPHABET": "GOOG"}),
        overrides={"ALPHABET INC": "GOOGL"},
    )
    assert mapper.match("Alphabet Inc") == ("GOOGL", "override")
