# Security Policy

## Supported versions

OpsPilot is pre-alpha and has no supported release. Security fixes are applied only to the latest commit on `main`. Do not deploy the project to production or give it production credentials.

| Version | Supported |
|---|---|
| Latest `main` | Security reports accepted |
| Tags and older commits | Not supported |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability and do not include secrets, exploit details, private endpoints, or production data in public discussions.

Submit a private report through [GitHub Security Advisories](https://github.com/standardforever/ops_pilot/security/advisories/new). Include:

- The affected commit, component, and configuration
- Reproduction steps using synthetic data
- Expected and observed behavior
- Security impact and realistic attack conditions
- Suggested mitigation, if known

You should receive acknowledgement within five business days. Triage will determine severity, affected versions, remediation, disclosure timing, and whether a CVE is appropriate. Please allow a reasonable remediation period before public disclosure.

## Security expectations

- Use synthetic data and least-privilege test environments.
- Never commit credentials or real operational data.
- Do not test against systems you do not own or have permission to assess.
- Preserve the read-only boundary unless an accepted architecture decision and explicit issue authorize a change.

