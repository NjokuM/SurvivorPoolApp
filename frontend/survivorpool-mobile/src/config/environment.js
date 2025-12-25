// Environment Configuration
// Set via EAS build profiles or fallback to default

const ENVIRONMENTS = {
  local: {
    API_BASE_URL: 'http://192.168.1.168:8001',
    name: 'Local Development',
  },
  int: {
    API_BASE_URL: 'https://survivorpoolapp-int.up.railway.app',
    name: 'Integration',
  },
  prod: {
    API_BASE_URL: 'https://survivorpoolapp.up.railway.app', // Update when you have prod URL
    name: 'Production',
  },
};

// ============================================================
// ENVIRONMENT SELECTION
// Priority: EAS build env var > manual override > default
// ============================================================
// For EAS builds: Set APP_ENV in eas.json build profiles
// For local dev: Change DEFAULT_ENV below
// ============================================================
const DEFAULT_ENV = 'int'; // Fallback for local development

// Read from EAS build environment variable if available
const CURRENT_ENV = process.env.APP_ENV || DEFAULT_ENV;
// ============================================================

const config = ENVIRONMENTS[CURRENT_ENV];

if (!config) {
  console.warn(`Invalid environment: ${CURRENT_ENV}, falling back to 'int'`);
}

const finalConfig = config || ENVIRONMENTS.int;

console.log(`🌍 Environment: ${finalConfig.name}`);
console.log(`🔗 API URL: ${finalConfig.API_BASE_URL}`);

export const API_BASE_URL = finalConfig.API_BASE_URL;
export const ENV_NAME = finalConfig.name;
export const IS_PRODUCTION = CURRENT_ENV === 'prod';
export const IS_LOCAL = CURRENT_ENV === 'local';

export default finalConfig;
