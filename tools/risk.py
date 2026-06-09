#!/usr/bin/env python3
"""Risk helpers shared by ClawTrader tools."""


def score_capital_fraction(score, btc_bearish=False):
    if score <= 6:
        return 0.0
    if score == 7:
        fraction = 0.50
    else:
        fraction = 0.85
    return fraction / 2 if btc_bearish else fraction


def reward_risk(entry, stop_loss, take_profit, side="long"):
    entry = float(entry)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)
    side = side.lower()
    if side == "long":
        risk = entry - stop_loss
        reward = take_profit - entry
    else:
        risk = stop_loss - entry
        reward = entry - take_profit
    if risk <= 0:
        return 0.0
    return reward / risk


def validate_trade(entry, current_price, stop_loss, take_profit, score, capital, requested_amount=None, btc_bearish=False, side="long", min_rr=1.2):
    entry = float(entry)
    current_price = float(current_price)
    capital = float(capital)
    requested_amount = float(requested_amount) if requested_amount is not None else None

    reasons = []
    max_fraction = score_capital_fraction(int(score), btc_bearish=btc_bearish)
    max_amount = round(capital * max_fraction, 2)

    if max_fraction <= 0:
        reasons.append("score must be 7 or higher")
    if current_price > entry * 1.02:
        reasons.append("current price is more than 2% above suggested entry")
    rr = reward_risk(entry, stop_loss, take_profit, side=side)
    if rr < min_rr:
        reasons.append(f"reward/risk {rr:.2f} is below minimum {min_rr:.2f}")
    if requested_amount is not None and requested_amount > max_amount:
        reasons.append(f"requested amount {requested_amount:.2f} exceeds max {max_amount:.2f}")

    return {
        "approved": not reasons,
        "reasons": reasons,
        "rr": round(rr, 2),
        "max_amount": max_amount,
        "score_capital_fraction": max_fraction,
        "btc_bearish": bool(btc_bearish),
    }

