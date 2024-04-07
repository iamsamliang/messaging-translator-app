import { PUBLIC_INITIAL_CONVERSATION_LOAD_LIMIT, PUBLIC_INITIAL_MSG_LOAD_LIMIT, PUBLIC_FETCH_MSG_BATCH_SIZE, PUBLIC_API_BASE_URL, PUBLIC_RECAPTCHA_SITE_KEY, PUBLIC_WEBSOCKET_BASE_URL } from '$env/static/public'

// Define a TypeScript interface for the configuration
interface ClientSettings {
  initialConversationLoadLimit: number;
  initialMessageLoadLimit: number;
  fetchMsgBatchSize: number;
  apiBaseURL: string;
  reCaptchaSiteKey: string;
  websocketBaseUrl: string;
}

// Implement the configuration with environment variables
const clientSettings: ClientSettings = {
  initialConversationLoadLimit: parseInt(PUBLIC_INITIAL_CONVERSATION_LOAD_LIMIT),
  initialMessageLoadLimit: parseInt(PUBLIC_INITIAL_MSG_LOAD_LIMIT),
  fetchMsgBatchSize: parseInt(PUBLIC_FETCH_MSG_BATCH_SIZE),
  apiBaseURL: PUBLIC_API_BASE_URL,
  reCaptchaSiteKey: PUBLIC_RECAPTCHA_SITE_KEY,
  websocketBaseUrl: PUBLIC_WEBSOCKET_BASE_URL,
};

// Assert all necessary configurations are set
function validateConfig(settings: ClientSettings): asserts settings is Required<ClientSettings> {
  const missingOrInvalidKeys = Object.entries(settings).filter(([key, value]) => 
    value === undefined || (key === 'initialConversationLoadLimit' && isNaN(value))
  ).map(([key]) => key);

  if (missingOrInvalidKeys.length > 0) {
    throw new Error(`Missing or invalid settings keys: ${missingOrInvalidKeys.join(', ')}`);
  }
}

// Validate to ensure all environment variables are loaded
validateConfig(clientSettings);

export default clientSettings;
