from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.odds_winner.ev")

class EvCalculator:
    """Encapsulates EV calculation logic (single responsibility)."""

    @staticmethod
    def implied_probability(decimal_odds: float) -> float:
        return 1.0 / decimal_odds if decimal_odds and decimal_odds != 0 else 0.0

    @staticmethod
    def expected_value(decimal_odds: float, est_prob: float, stake: float = 1.0) -> float:
        payout = (decimal_odds - 1.0) * stake
        return (est_prob * payout) - ((1.0 - est_prob) * stake)

    @staticmethod
    def worth_betting(decimal_odds: float, est_prob: float, stake: float = 1.0) -> bool:
        return EvCalculator.expected_value(decimal_odds, est_prob, stake) > 0.0
