"""subscription_has_dvr — gates whether recording entities/services get
created at all (see coordinator.py), so a false negative silently hides
a whole feature set and a false positive creates entities that 403."""
from .helpers import const


class TestSubscriptionHasDvr:
    def test_perfect(self):
        assert const.subscription_has_dvr("Perfect") is True

    def test_perfect_plus_with_bundle_suffix(self):
        assert const.subscription_has_dvr("Perfect Plus mit WOW Filme & Serien Jahrespaket") is True

    def test_o2_tv_l(self):
        assert const.subscription_has_dvr("O2 TV L") is True

    def test_o2_tv_xl_matches_via_l_substring(self):
        assert const.subscription_has_dvr("O2 TV XL") is True

    def test_case_insensitive(self):
        assert const.subscription_has_dvr("PERFECT") is True

    def test_plain_tier_without_dvr(self):
        assert const.subscription_has_dvr("Comfort") is False

    def test_empty_string(self):
        assert const.subscription_has_dvr("") is False

    def test_none_does_not_raise(self):
        assert const.subscription_has_dvr(None) is False
