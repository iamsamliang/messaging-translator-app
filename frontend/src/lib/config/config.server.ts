// Load environment variables from .env file
import 'dotenv/config'

// Define a TypeScript interface for the configuration
interface ServerConfig {
  apiBaseURL: string;
  RECAPTCHA_SECRET_KEY: string;
  RATE_LIMITER_REDIS_TOKEN: string;
  RATE_LIMITER_REDIS_URL: string;
}

// Implement the configuration with environment variables
const serverSettings: ServerConfig = {
  apiBaseURL: process.env.VITE_API_BASE_URL!,
  RECAPTCHA_SECRET_KEY: process.env.RECAPTCHA_SECRET_KEY!,
  RATE_LIMITER_REDIS_TOKEN: process.env.RATE_LIMITER_REDIS_TOKEN!,
  RATE_LIMITER_REDIS_URL: process.env.RATE_LIMITER_REDIS_URL!
};

// Assert all necessary configurations are set
function validateConfig(settings: ServerConfig): asserts settings is Required<ServerConfig> {
  const missingKeys = Object.entries(settings).filter(([, value]) => value === undefined).map(([key]) => key);
  if (missingKeys.length > 0) {
    throw new Error(`Missing settings keys: ${missingKeys.join(', ')}`);
  }
}

// Validate to ensure all environment variables are loaded
validateConfig(serverSettings);

export default serverSettings;
