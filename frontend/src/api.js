import axios from "axios";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function explainPost({ post_content, image_url, context_limit = 10, debug = false }) {
  const { data } = await axios.post(`${API_BASE_URL}/explain`, {
    post_content,
    image_url: image_url || null,
    context_limit,
    debug,
  });
  return data;
}

export async function socialQA({ question, sources_type = "all", debug = false }) {
  const { data } = await axios.post(`${API_BASE_URL}/social-qa`, {
    question,
    sources_type,
    debug,
  });
  return data;
}

export async function healthCheck() {
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
}

