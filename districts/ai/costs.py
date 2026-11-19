# coding=utf-8
"""Estimated costs of the AI assistant (OpenSpec change ai-chat-panel, D6). Prices change: the table names its date and
the tab labels every cost as an estimate."""

PRICES_DATE = '2026-11-03'
# USD per million tokens: input, cache write (5 min), cache read, output
PRICES = {
    'claude-opus-5-5': (4.00, 5.00, 0.20, 20.00),
    'claude-sonnet-5-5': (2.00, 2.50, 0.10, 10.00),
    'claude-haiku-5-5': (0.10, 0.125, 0.01, 0.50),
    # models a refusal fallback may serve a step with
    'claude-opus-5': (5.00, 6.25, 0.50, 25.00),
    'claude-opus-4-8': (5.00, 6.25, 0.50, 25.00),
    'claude-sonnet-5': (2.00, 2.50, 0.20, 10.00),
}
MODELS = ('claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5')
DEFAULT_MODEL = 'claude-opus-5-5'
DEFAULT_LIMIT_USD = 2.0


def _tokens(usage, name):
    value = getattr(usage, name, None) if not isinstance(usage, dict) else usage.get(name)
    return int(value or 0)


def stepCost(model, usage, fallback_model=DEFAULT_MODEL):
    """(USD, priced exactly) of one request from its usage; an unknown model is priced like fallback_model"""
    known = model in PRICES
    p_in, p_write, p_read, p_out = PRICES[model if known else fallback_model]
    usd = (_tokens(usage, 'input_tokens') * p_in + _tokens(usage, 'cache_creation_input_tokens') * p_write
           + _tokens(usage, 'cache_read_input_tokens') * p_read + _tokens(usage, 'output_tokens') * p_out) / 1e6
    return usd, known


class SessionCosts:
    """costs of the conversation steps, the answer in progress and the limit of the session"""

    def __init__(self, limit=DEFAULT_LIMIT_USD):
        self.limit = float(limit)
        self.step = float(limit)
        self.total = 0.0
        self.answer = 0.0
        self.unknown_models = set()

    def startAnswer(self):
        self.answer = 0.0

    def add(self, model, usage, session_model):
        usd, known = stepCost(model, usage, session_model if session_model in PRICES else DEFAULT_MODEL)
        if not known:
            self.unknown_models.add(model)
        self.total += usd
        self.answer += usd
        return usd

    def overLimit(self):
        return self.total >= self.limit

    def raiseLimit(self):
        """'Continue' at the limit: the limit grows by its initial amount"""
        self.limit += self.step
