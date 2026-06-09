---
name: broker-safety
description: Evaluates platform, credential, automation, API, broker, execution, withdrawal, demo, real-money, and operational-security risks.
---

# Broker Safety

Use this skill when the user mentions brokers, platforms, Binance, APIs, bots, automation, real money, credentials, or execution.

## Objective

Protect the user from technical, operational, legal, and security risk.

## Rules

- Do not ask for passwords.
- Do not ask for 2FA codes.
- Do not store private keys.
- Do not recommend sharing sensitive credentials.
- Warn before using unofficial APIs or fragile automation.
- Do not connect real money without prior validation.
- Prefer official APIs, testnet, paper trading, and limited permissions.
- Never enable withdrawal permissions.

## Integration Risk

Green: official API, clear docs, testnet/demo, limited permissions.

Yellow: partial API, data available, execution unclear.

Red: unofficial API, insecure credentials, scraping, uncontrolled real execution.

## Output

```
Platform:
API status:
Credential risk:
Execution risk:
Recommended mode:
Blocked actions:
Conclusion:
```

