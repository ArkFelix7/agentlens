# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a security issue, please open a [GitHub Security Advisory](https://github.com/ArkFelix7/agentlens/security/advisories/new) in this repository. This keeps the report private until a fix is ready.

Include:

- A clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Any suggested fix or mitigation

## Response Timeline

- **Acknowledgement**: within 48 hours
- **Initial assessment**: within 5 business days
- **Fix and disclosure**: coordinated with the reporter, typically within 30 days depending on severity

## Scope

This policy covers:

- `agentlens-sdk` (Python SDK)
- `agentlens-server` (observability server)
- `agentlens-mcp` (MCP server)
- `@agentlens-sdk/sdk` (TypeScript SDK)

Out of scope: vulnerabilities in third-party dependencies should be reported to their respective maintainers.
