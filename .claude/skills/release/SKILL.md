---
name: release
description: Publish a new version of the iOS app to the App Store - bump the version, run the production EAS build with automatic upload to App Store Connect, write the "What's New" text, and walk the user through submitting for review. Use when the user says "get this to the App Store", "release it", "publish the app" or runs /release.
---

# Release to the App Store

## 1. Make sure main is ready

- Everything meant for this release is merged into `main` and the user has tested it on their phone. Nothing unmerged sneaks in: build from `main`.
- If the release depends on backend changes, confirm they're deployed (`/version` on prod shows the latest backend commit).
- Check anything user-facing that depends on server config actually works on prod (e.g. forgot-password needs the `SMTP_*` variables in Railway). Flag gaps before release - Apple reviewers try the features.

## 2. Find the last release

From `frontend/survivorpool-mobile`:
```
eas build:list --platform ios --buildProfile production --limit 3 --non-interactive --json
```
Note the last `appVersion` and `appBuildVersion`, and its `gitCommitHash` - that's where the release notes start.

## 3. Bump the version

`eas.json` uses `"appVersionSource": "local"`, so the version lives in `app.json`:
- `expo.version`: new features → minor bump (1.1.0 → 1.2.0); fixes only → patch (1.1.0 → 1.1.1).
- `expo.ios.buildNumber`: always +1 from the last production build. Never reuse one - App Store Connect rejects it.

Do it on a branch (`chore/release-<version>`), commit `chore(release): bump iOS to <version> (build <n>)`, merge into `main`, delete the branch.

## 4. Build and upload

```
eas build -p ios --profile production --auto-submit --non-interactive --no-wait
```
This builds and then uploads to App Store Connect (app id `6757318859`). Give the user the build and submission links, and watch the build in the background until it finishes.

## 5. Write "What's New"

From `git log --oneline <last release commit>..main`, pick the `feat` and user-visible `fix` commits and turn them into short bullet points **written for players**, not developers - what they can now do, no file names or jargon. Put the most exciting change first. Give it in a code block, ready to paste.

## 6. Tell the user the App Store Connect steps

Uploading doesn't submit for review. They need to:
1. Wait for Apple to process the build (10-30 min) - it appears under **TestFlight**.
2. Under **App Store**, add a new version with the same number, select the build, and paste "What's New".
3. Tap **Submit for Review**.

## 7. Afterwards

Note the release in `internal-docs/bugfixes-and-features.md` (version, date, what's in it).
