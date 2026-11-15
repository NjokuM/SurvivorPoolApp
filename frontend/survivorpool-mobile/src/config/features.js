// App feature flags - flip to bring a feature back without a code change
// elsewhere. Shipped with the app build, so a change needs a new build.
export const FEATURES = {
  // The old History tab. Its "by week" view now lives in Summary's picks
  // card (with gameweek arrows) and "by player" in Standings (tap a row).
  historyTab: false,
};
