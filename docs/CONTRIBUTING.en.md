# Contributing to ClawTrader

Thank you for wanting to contribute. ClawTrader is an open source project for building a configurable, safe, and easy-to-install trading assistant. Because it touches APIs, credentials, and possible financial execution, contribution rules are stricter than in a normal project.

## Principles

- Security first.
- Live trading disabled by default.
- Portable code, with no personal paths.
- Honest documentation: do not promise profits.
- Spanish and English skills must keep the same structure.
- Small, clear, reviewable changes.

## Mandatory Rules

Do not commit credentials or sensitive data:

```text
.env
API keys
secret keys
Telegram tokens
personal accounts
real balances
private session files
```

Do not hardcode local paths:

```text
No: /home/user/...
No: C:\Users\...
Yes: Path.home() / ".openclaw" / "workspace"
```

Do not enable live trading by default. Any order-related change must respect:

```env
CLAWTRADER_DRY_RUN=true
CLAWTRADER_LIVE_TRADING=false
```

Do not add logic that sends real orders without validation, risk control, and explicit configuration confirmation.

## Project Structure

```text
tools/        Python scripts and utilities
skills/es/    Spanish skills
skills/en/    English skills
docs/es/      Spanish documentation
docs/en/      English documentation
install.py    Interactive installer
deploy.sh     Skills/tools deployment
```

If you add a skill under `skills/es`, add its equivalent under `skills/en`. If you add documentation under `docs/es`, add its equivalent under `docs/en`.

## Recommended Workflow

1. Fork the project.
2. Create a branch with a clear name:

```bash
git checkout -b fix/install-paths
git checkout -b feat/new-risk-check
git checkout -b docs/contributing-guide
```

3. Make small changes.
4. Run local checks.
5. Open a pull request explaining what changed and how you tested it.

## Minimum Checks

Before sending a PR:

```bash
python3 -m compileall -q install.py tools
python3 tools/clawtrader.py health
python3 tools/clawtrader.py scan --symbols BTCUSDT ETHUSDT
```

To test installation without touching your real configuration:

```bash
tmp=$(mktemp -d)
HOME="$tmp" python3 install.py
```

If you modify the dashboard:

```bash
python3 tools/clawtrader.py dashboard --host 127.0.0.1 --port 8765
curl -s http://127.0.0.1:8765/health
```

## Rules For Python Tools

- Use `Path.home()` and configurable paths.
- Load `.env` with `tools/load_env.py`.
- Do not hardcode credentials.
- Do not write state to `/tmp` if it can live in `~/.openclaw/workspace/state`.
- Keep `dry-run` as the safe default.
- Handle API errors without crashing the process.
- Avoid new dependencies unless they are necessary.

## Rules For Skills

Each skill must include front matter:

```yaml
---
name: skill-name
description: Clear, brief description.
---
```

Skills must:

- Be specific.
- Avoid profitability promises.
- Include risk rules when relevant.
- Have ES/EN equivalents.
- Avoid personal names, local paths, and private data.
- Mark compatibility-only skills as `[LEGACY]`.

## Rules For Documentation

Documentation must:

- Explain reproducible steps.
- Never ask users to print secrets in the console.
- Never present base64 as encryption.
- Distinguish demo, paper trading, and live trading.
- Clearly state that trading involves risk of capital loss.

## Pull Requests

A good PR includes:

- Short summary.
- Files changed.
- Risks of the change.
- Verification commands executed.
- Screenshots or logs when relevant.

Suggested template:

```markdown
## Summary

## Changes

## Risks

## Verification
- [ ] python3 -m compileall -q install.py tools
- [ ] python3 tools/clawtrader.py health
- [ ] Installation tested in a temporary HOME
```

## Security Changes

If the PR touches order execution, credentials, API permissions, Binance, Alpaca, or Telegram, it must explain:

- What permissions it needs.
- How it avoids accidental live trading.
- What happens when credentials are missing.
- How the result is audited.
- How it can be reverted or disabled.

## Community

A Discord server for ideas, support, and contributions is coming soon.

In the meantime, you can send a Discord message to:

```text
gilbertmax
```

## License

By contributing, you agree that your changes will be published under the project's MIT License.
