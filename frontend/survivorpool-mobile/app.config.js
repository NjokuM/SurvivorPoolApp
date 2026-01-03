// Dynamic Expo config - allows environment variables to be injected at build time
export default ({ config }) => {
  return {
    ...config,
    extra: {
      ...config.extra,
      APP_ENV: process.env.APP_ENV || 'local',
    },
  };
};
