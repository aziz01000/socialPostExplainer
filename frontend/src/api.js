import axios from "axios";

const isLocalhost =
  typeof window !== "undefined" &&
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || (isLocalhost ? "http://localhost:8000" : "");

function buildApiUrl(path) {
  if (!API_BASE_URL) {
    throw new Error(
      "Backend URL is not configured for this deployment. Set REACT_APP_API_BASE_URL in GitHub Actions Variables."
    );
  }
  return `${API_BASE_URL}${path}`;
}

export async function ask({
  question,
  image_url = null,
  image_base64 = null,
  sources_type = "all",
  context_limit = 10,
  debug = false,
}) {
  const { data } = await axios.post(buildApiUrl("/ask"), {
    question,
    image_url,
    image_base64,
    sources_type,
    context_limit,
    debug,
  });
  return data;
}

export async function askWithUpload(formData) {
  const { data } = await axios.post(buildApiUrl("/ask/upload"), formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function healthCheck() {
  const { data } = await axios.get(buildApiUrl("/health"));
  return data;
}

