# Security Policy

## Overview

AlphaWEEX is an autonomous trading engine that handles sensitive API credentials and financial operations. This document outlines security best practices and guidelines for using the system safely.

## API Key Safety

### Critical Security Rules

1. **Never commit API keys to version control**
   - Always use `.env` file for credentials
   - The `.env` file is already in `.gitignore`
   - Never share your `.env` file publicly

2. **Use environment variables**
   - Store all sensitive credentials in `.env`
   - Use `python-dotenv` to load environment variables
   - Never hardcode credentials in source code

3. **Separate API keys by environment**
   - Use different API keys for development, testing, and production
   - Use paper trading/testnet credentials for testing
   - Keep production credentials on production servers only

### Recommended API Key Configuration

```bash
# .env file structure

# WEEX Exchange API
WEEX_API_KEY=your_weex_api_key_here
WEEX_API_SECRET=your_weex_api_secret_here
WEEX_API_PASSWORD=your_weex_api_password_here  # If required

# DeepSeek AI API
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Alpaca Market Data API (for TradFi Oracle)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
```

### API Key Permissions

Configure your exchange API keys with minimal required permissions:

- **WEEX Exchange:**
  - ✅ Enable: Read account balance
  - ✅ Enable: Place orders (spot trading only)
  - ✅ Enable: Cancel orders
  - ❌ Disable: Withdrawals (critical security measure)
  - ❌ Disable: Transfers to other accounts

- **Alpaca API:**
  - ✅ Use paper trading API for development
  - ✅ Enable: Market data access
  - ❌ Disable: Live trading (unless in production)

## Safe Mode & Error Handling

AlphaWEEX implements graceful degradation when API connections fail:

1. **API Connection Failures**
   - System automatically falls back to "Safe Mode"
   - Uses simulated/cached data instead of crashing
   - Logs all errors for debugging

2. **Kill-Switch Protection**
   - Automatically halts trading if equity drops > 3% in 1 hour
   - Prevents runaway losses
   - Can be configured via `KILL_SWITCH_THRESHOLD` in `.env`

3. **Stability Lock**
   - Prevents frequent strategy changes
   - 12-hour cooldown after each evolution
   - Configurable via `STABILITY_LOCK_HOURS` in `.env`

## Network Security

### Recommended Practices

1. **Use HTTPS/WSS only**
   - All API connections should use encrypted protocols
   - Never send credentials over unencrypted connections

2. **IP Whitelisting**
   - Configure IP whitelisting on exchange API keys when possible
   - Restrict API access to known server IPs

3. **Rate Limiting**
   - Respect exchange API rate limits
   - Implement exponential backoff on errors
   - Monitor API usage to avoid bans

## Code Security

### Best Practices

1. **Code Review**
   - All strategy evolutions are validated before deployment
   - Syntax and logic audits are performed automatically
   - Guardrails prevent unsafe code execution

2. **Adversarial Testing**
   - New strategies are tested against simulated flash crashes
   - Red Team audits validate risk management
   - Strategies must pass stress tests before approval

3. **Dependency Management**
   - Keep dependencies up to date
   - Regularly audit `requirements.txt` for vulnerabilities
   - Use `pip-audit` or similar tools

## Incident Response

### If API Keys are Compromised

1. **Immediate Actions:**
   - Revoke compromised API keys immediately on the exchange
   - Generate new API keys
   - Update `.env` file with new credentials
   - Monitor account for unauthorized activity

2. **Investigation:**
   - Review git history for accidental commits
   - Check logs for suspicious API calls
   - Verify no unauthorized code changes

3. **Prevention:**
   - Use git hooks to prevent committing `.env` files
   - Implement secret scanning in CI/CD
   - Regular security audits

### Reporting Security Issues

If you discover a security vulnerability in AlphaWEEX:

1. **Do NOT open a public issue**
2. Email the maintainers privately
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Compliance & Best Practices

### Trading Regulations

- Ensure compliance with local trading regulations
- Use the system responsibly and within legal boundaries
- Understand risks associated with automated trading
- Never trade with funds you cannot afford to lose

### Data Privacy

- User data is stored locally only
- No data is sent to third parties except exchange/AI APIs
- Log files may contain sensitive information - protect them
- Regularly clean up old logs and backups

## Security Checklist

Before deploying AlphaWEEX:

- [ ] API keys stored in `.env` file (not in code)
- [ ] `.env` file added to `.gitignore`
- [ ] Exchange API keys have withdrawals disabled
- [ ] Kill-switch threshold configured appropriately
- [ ] Stability lock enabled (minimum 12 hours)
- [ ] Using paper trading/testnet for initial testing
- [ ] IP whitelisting configured on exchange API keys
- [ ] Dependencies are up to date and audited
- [ ] Logs are secured and regularly rotated
- [ ] Monitoring and alerts configured

## Updates & Patches

- Monitor repository for security updates
- Apply security patches promptly
- Subscribe to exchange API security bulletins
- Keep Python and dependencies updated

## Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)
- [CCXT Security](https://docs.ccxt.com/#/README?id=api-keys-setup)

---

**Remember:** Security is a shared responsibility. Always follow best practices and stay informed about potential threats.
