---
name: phone-build
description: Build the app from the current branch and put it on the user's iPhone for testing - starts an EAS preview build, watches it, and hands over the install link with what to test. Use when the user wants to try changes on their phone, says "make a build", "put it on my phone" or runs /phone-build.
---

# Phone build

The `preview` profile is an internal-distribution iOS build that talks to the **prod** backend. The user's iPhone ("My Phone") is already registered (Apple team `923W8ZK3JX`).

## 1. Before building

- Commit any app changes on the current branch and push it - the build should match something in git.
- If the change needs **backend** changes that aren't on prod yet, the features won't work in the build. Say so and ask whether to `/ship` the backend first.

## 2. Start the build

From `frontend/survivorpool-mobile`:
```
eas build -p ios --profile preview --non-interactive --no-wait
```
Grab the `https://expo.dev/accounts/njokum/projects/survivorpool-mobile/builds/<id>` link from the output.

## 3. Tell the user straight away

- The link: open it **in Safari on the iPhone** and tap Install. It takes ~15 minutes to be ready.
- **What to test** - a short numbered list of the exact things that changed and where to find them in the app (tab, button, what should happen).
- Any known limitation (e.g. "points pools only", "needs the backend deploy").

## 4. Watch it

Run a background loop polling the build's status, e.g.
```
eas build:view <id> --json   # .status: FINISHED | ERRORED | CANCELED
```
every ~30 s, and when it finishes tell the user it's ready (or, if it errored, fetch the logs link and explain the failure).

## 5. After they test

Once the user approves on device, `/ship` merges the branch. If they want changes, make them, push, and build again.
