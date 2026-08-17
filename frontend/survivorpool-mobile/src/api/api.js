import axios from "axios";
import { API_BASE_URL } from "../config/environment";
import { getAccessToken, getRefreshToken, storeTokens, clearAuth } from "../utils/tokenStorage";

const API = axios.create({
    baseURL: API_BASE_URL,
});

// App.js registers a listener here so it can send the user back to the
// Login screen if the refresh token itself has expired (e.g. after a
// season of inactivity) and silent refresh is no longer possible.
export const authEvents = {
    onSessionExpired: null,
};

// Attach the current access token to every outgoing request.
API.interceptors.request.use(async (config) => {
    const token = await getAccessToken();
    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// If a request comes back 401 (expired access token), silently exchange the
// refresh token for a new pair and retry the request once. This is what
// keeps users logged in without re-entering credentials all season.
let refreshPromise = null;

API.interceptors.response.use(
    (response) => response,
    async (error) => {
        const { config, response } = error;
        if (
            !config ||
            response?.status !== 401 ||
            config._retried ||
            config.url === "/login" ||
            config.url === "/refresh"
        ) {
            return Promise.reject(error);
        }

        const refreshToken = await getRefreshToken();
        if (!refreshToken) {
            // No refresh token to fall back on — the session is gone either way.
            await clearAuth();
            if (authEvents.onSessionExpired) {
                authEvents.onSessionExpired();
            }
            return Promise.reject(error);
        }

        config._retried = true;
        try {
            if (!refreshPromise) {
                const formData = new FormData();
                formData.append("refresh_token", refreshToken);
                refreshPromise = axios
                    .post(`${API_BASE_URL}/refresh`, formData, {
                        headers: { "Content-Type": "multipart/form-data" },
                    })
                    .finally(() => {
                        refreshPromise = null;
                    });
            }
            const { data } = await refreshPromise;
            await storeTokens(data.access_token, data.refresh_token);
            config.headers = { ...config.headers, Authorization: `Bearer ${data.access_token}` };
            return API(config);
        } catch (refreshError) {
            await clearAuth();
            if (authEvents.onSessionExpired) {
                authEvents.onSessionExpired();
            }
            return Promise.reject(error);
        }
    }
);

export default API;

