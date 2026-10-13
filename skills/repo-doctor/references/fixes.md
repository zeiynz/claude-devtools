# Fix recipes

## Leaked secret
1. **Rotate the credential first.** Removing it from git does not make it safe; assume it is compromised.
2. Remove from code; load from environment variables.
3. Purge history: `git filter-repo --path <file> --invert-paths` (or BFG), then force-push and ask collaborators to re-clone.
4. Add `.env` and key files to `.gitignore`. Enable GitHub secret scanning + push protection.

## Minimal CI (Python)
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python -m unittest discover -s tests -v
```

## README that earns stars
Order: one-line value → demo (GIF/screenshot) → install in <=3 commands → usage example → how it works → contributing → license.

## Files worth adding
LICENSE (MIT/Apache-2.0), CONTRIBUTING.md, SECURITY.md (how to report), CHANGELOG.md (Keep a Changelog), `.github/ISSUE_TEMPLATE/`.
