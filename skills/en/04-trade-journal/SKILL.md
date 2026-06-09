---
name: trade-journal
description: Structures trading journals, records trades, detects repeated mistakes, and turns demo or paper results into operational learning.
---

# Trade Journal

Use this skill when the user wants to register, review, or learn from trades.

## Objective

Build operational memory. A trader improves by measuring decisions, not only results.

## Required Fields

- Date
- Time
- Platform
- Asset
- Timeframe
- Trade type
- Direction
- Entry reason
- Market context
- Entry price
- Stop loss
- Take profit
- Exit price
- Result
- Mistake, if any
- Lesson

## Review Rules

- A winning trade can still be bad process.
- A losing trade can still be good process.
- Classify trades as A, B, C, D, or F.
- Detect repeated errors before suggesting new strategies.

## Output

Write clear structured entries suitable for `memory/YYYY-MM-DD.md`.

