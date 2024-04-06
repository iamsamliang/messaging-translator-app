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
  initialConversationLoadLimit: parseInt(import.meta.env.VITE_INITIAL_CONVERSATION_LOAD_LIMIT),
  initialMessageLoadLimit: parseInt(import.meta.env.VITE_INITIAL_MSG_LOAD_LIMIT),
  fetchMsgBatchSize: parseInt(import.meta.env.VITE_FETCH_MSG_BATCH_SIZE),
  apiBaseURL: import.meta.env.VITE_API_BASE_URL,
  reCaptchaSiteKey: import.meta.env.VITE_RECAPTCHA_SITE_KEY,
  websocketBaseUrl: import.meta.env.VITE_WEBSOCKET_BASE_URL,
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
