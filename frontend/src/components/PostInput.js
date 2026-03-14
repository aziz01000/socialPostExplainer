/**
 * PostInput Component - Input form for social media posts
 */

import React, { useState } from "react";
import "./PostInput.css";

function PostInput({ onSubmit, isLoading }) {
  const [post, setPost] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!post.trim()) {
      setError("Please enter a post");
      return;
    }

    try {
      await onSubmit(post, imageUrl || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="post-input-form">
      <div className="form-group">
        <label htmlFor="post">Social Media Post:</label>
        <textarea
          id="post"
          value={post}
          onChange={(e) => setPost(e.target.value)}
          placeholder="Enter a social media post..."
          rows={5}
          disabled={isLoading}
          className="post-textarea"
        />
      </div>

      <div className="form-group">
        <label htmlFor="image-url">Image URL (optional):</label>
        <input
          id="image-url"
          type="url"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          placeholder="https://example.com/image.jpg"
          disabled={isLoading}
          className="image-url-input"
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button type="submit" disabled={isLoading} className="submit-button">
        {isLoading ? "Explaining..." : "Explain Post"}
      </button>
    </form>
  );
}

export default PostInput;
