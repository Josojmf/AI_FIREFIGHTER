# STG Branch Information

## Summary
The `stg` branch has been successfully created with the file `FO/insert.py` completely removed from all git history.

## Changes Made
1. Created new branch `stg` from the current codebase
2. Removed `FO/insert.py` from the working directory
3. Used `git filter-branch` to remove `FO/insert.py` from all git history
4. Cleaned up git references and ran garbage collection
5. Verified the file no longer exists in any commit

## Workflow Prevention
The `stg` branch will NOT trigger any GitHub Actions workflows because:
- CI workflow (`ci.yml`) only triggers on: `main`, `develop` branches
- CD workflow (`cd.yml`) only triggers on: `main` branch
- Security workflow (`security.yml`) triggers on: `main`, `develop` branches
- Quality gates (`quality-gates.yml`) triggers on: `main`, `develop` branches

The `stg` branch is not listed in any workflow triggers, so pushing to it will not execute any workflows.

## To Use the STG Branch
The stg branch exists locally with all history cleaned. To push it to remote:
```bash
git push -u origin stg --force-with-lease
```

Note: This requires force push since history was rewritten.
