---
name: ship
description: Finish the current change and deploy it - run the backend tests, review backend changes, commit with conventional commits, push the branch, merge to main, confirm int and prod are running the new commit, then delete the branch. Use when the user says "ship it", "merge it", "commit and push", "deploy this" or runs /ship.
---

# Ship

Merging to `main` deploys **both int and prod** on Railway at once, and migrations run on container start - a broken one takes the whole backend down. So this skill refuses to merge on any failed check.

## 1. Check where we are

- `git branch --show-current` - if on `main`, stop: create a branch first (`feat/...`, `fix/...`, `chore/...`) and move the changes onto it.
- `git status --short` - work out which files belong to this change. The user keeps unrelated uncommitted edits (e.g. `frontend/survivorpool-mobile/eas.json`, `.gitignore`) out of commits; **stage by path, never `git add -A`**.

## 2. Tests (stop on failure)

- If anything under `backend/` changed: `backend/venv/bin/python -m pytest -q` (takes ~2 min; give it a 300000 ms timeout). Every test must pass. If one fails, stop and report the output - don't merge.
- New backend behaviour must come with tests. If the change has none, write them first.
- If a migration was added: `cd backend && venv/bin/alembic heads` must show exactly **one** head.
- For changed app files (no Jest yet), syntax-check each one:
  `node -e "require('@babel/core').transformFileSync('<file>',{presets:['@babel/preset-react'],babelrc:false,configFile:false})"` from `frontend/survivorpool-mobile`.

## 3. Review backend changes

If `backend/` changed, run the `backend-change-reviewer` agent on the diff against `main`. Fix any **blocking** finding before continuing; mention the rest to the user.

## 4. Commit and push

- Conventional commits, e.g. `feat(pools): ...`, `fix(notifications): ...`. Backend and app changes go in separate commits.
- End each message with the co-author line from the current attribution instructions.
- `git push -u origin <branch>`.

## 5. Hold or merge?

**Don't merge yet** if the change is app UI the user hasn't seen on their phone - offer `/phone-build` instead and stop here. Backend-only fixes and changes they've already approved on device can go ahead.

Otherwise:
```
git checkout main && git pull
git merge --no-ff <branch> -m "Merge branch '<branch>'"
git push origin main
```

## 6. Confirm the deploy

Only needed when `backend/` changed (app-only changes reach phones through a build, not Railway).

Note the merge commit: `git rev-parse HEAD`. Then wait with Monitor (or a background loop - foreground `sleep` is blocked) until both report it:
```
curl -s https://survivorpoolapp-int.up.railway.app/version
curl -s https://survivorpoolapp-production.up.railway.app/version
```
`{"commit": "<sha>"}` matching the merge commit means it's live. If `commit` is `null` (Railway didn't set the variable), fall back to checking that a new endpoint now returns something other than 404, or that `/docs` returns 200. Give up after ~10 minutes and report - a container stuck restarting usually means a migration failed.

## 7. Clean up

```
git branch -d <branch>
git push origin --delete <branch>
```

## 8. Report

Short: what shipped, tests passed (count), deploy confirmed (or not, and why), branch deleted, anything the user must do (e.g. set an env var, reopen the app, make a new build for app changes).
