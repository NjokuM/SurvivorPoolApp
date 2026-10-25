// "+3" / "0" / "-2" - the sign makes goal difference readable at a glance.
export const formatGoalDifference = (gd) => {
  const value = gd || 0;
  return value > 0 ? `+${value}` : `${value}`;
};
