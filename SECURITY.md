# Security

Skills in this collection are instructions for AI agents, not hosted services
or dependency bundles. Optional `scripts/` helpers are local, stdlib Python:
they do not phone home, fetch remote payloads, or send telemetry.

Treat skill text the same way you would treat a shell snippet from a stranger.
Review what an agent would run before installing a fork, and do not paste
secrets into skill files or helper arguments.

## Reporting a vulnerability

Do not open a public issue for a dangerous skill instruction, helper injection
path, or other security problem.

Report privately using GitHub's private vulnerability reporting on this
repository, or contact the maintainer through the GitHub profile on this
project. Include:

- which skill or helper is affected
- what an agent or user would do that causes harm
- a minimal reproduction if you have one
