const normalizeBaseUrl = (value: string) => {
  if (!value) {
    return '';
  }
  return value.endsWith('/') ? value.slice(0, -1) : value;
};

const defaultBaseUrl = 'http://localhost:8000';

const envBaseUrl =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  process.env.API_BASE_URL ??
  defaultBaseUrl;

export const API_BASE_URL = normalizeBaseUrl(envBaseUrl);
