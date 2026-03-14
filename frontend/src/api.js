/**
 * Configuration for making API calls to the backend.
 */

import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Send a post to the backend for explanation.
 * @param {string} post - The social media post
 * @param {string} imageUrl - Optional image URL
 * @returns {Promise} The explanation response
 */
export async function explainPost(post, imageUrl) {
  try {
    const response = await apiClient.post("/explain", {
      post,
      image_url: imageUrl || null,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to explain post"
      );
    }
    throw error;
  }
}

/**
 * Check if the backend is healthy.
 * @returns {Promise<boolean>} Whether backend is healthy
 */
export async function healthCheck() {
  try {
    const response = await apiClient.get("/health");
    return response.data.status === "healthy";
  } catch (error) {
    return false;
  }
}
