# ShortsBot Git & GitHub Best Practices Workflow

This document outlines the professional standards we apply to managing the ShortsBot repository.

## 1. Branch Naming Conventions
Never push directly to the `main` branch. Always create a descriptive branch:
- **Features**: `feat/add-auto-scheduler`
- **Bug Fixes**: `fix/upload-loop-crash`
- **Documentation**: `docs/update-readme`
- **Maintenance/Refactoring**: `chore/cleanup-imports` or `refactor/api-failover`

## 2. Conventional Commits
Commit messages should tell a story and be easily filtered. We use the conventional commit specification format: `<type>: <description>`
- `feat: add telegram remote control bypass`
- `fix: resolve yt-dlp timeout errors on viral mode`
- `chore: update requirements.txt`
- `docs: attach aws deployment diagram`

## 3. Atomic Commits
Keep your commits small and focused on a single change. Do not put 15 different bug fixes into a single `git commit -m "fixed lots of stuff"`. 
- Commit the UI change.
- Commit the Database change.
- Commit the Bug Fix independently.

## 4. The GitHub Flow (Pull Requests)
1. Branch off `main` (`git checkout -b feat/my-feature`).
2. Make your atomic commits.
3. Push the branch (`git push origin feat/my-feature`).
4. Open a **Pull Request (PR)** on GitHub to merge into `main`. Review code before merging to protect production.

## 5. Security & Ignored Files
The local `.gitignore` is our first line of defense.
**NEVER** use `git add .` if there is a risk of a `.env` file, AWS key, or `client_secrets.json` being untracked in your folder. The `.gitignore` must always securely shield these.

## 6. Version Tagging (Releases)
When a milestone is reached or the project matches a stable state for AWS deployment, tag it.
`git tag v1.0.0`
`git push origin --tags`
This locks a snapshot that we can always roll back to if future features break the pipeline.
