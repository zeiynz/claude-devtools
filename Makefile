.PHONY: test lint package install audit clean
PY ?= python3

test:      ## run all tests
	$(PY) -m unittest discover -s tests -v
lint:      ## lint every skill
	$(PY) skills/skill-factory/scripts/lint_skill.py skills
package:   ## build dist/*.skill for claude.ai upload
	$(PY) skills/skill-factory/scripts/package_skill.py skills --out dist
install:   ## copy skills to ~/.claude/skills (Claude Code)
	./install.sh
audit:     ## dogfood: audit this repo
	$(PY) skills/repo-doctor/scripts/audit.py .
clean:
	rm -rf dist .pytest_cache; find . -name __pycache__ -type d -prune -exec rm -rf {} +
