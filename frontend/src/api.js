import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function ask({
  question,
  image_url = null,
  image_base64 = null,
  sources_type = "all",
  context_limit = 10,
  debug = false,
}) {
  const { data } = await axios.post(`${API_BASE_URL}/ask`, {
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
  const { data } = await axios.post(`${API_BASE_URL}/ask/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function healthCheck() {
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
}

