import axios from "axios";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function explainPost({ post_content, image_url }) {
  const resp = await axios.post(`${API_BASE_URL}/explain`, {
    post_content,
    image_url: image_url || null,
  });
  return resp.data;
}

