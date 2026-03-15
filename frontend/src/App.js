import React, { useState, useCallback } from "react";
import { ask, askWithUpload } from "./api";
import "./App.css";

function sourcePlatformLabel(platform) {
  if (!platform) return "source";
  if (platform === "vector_db") return "Vector DB";
  const labels = {
    newsdata: "NewsData",
    newsapi: "NewsAPI",
    guardian: "Guardian",
    reddit: "Reddit",
    twitter: "Twitter",
    web: "Web",
  };
  return labels[platform] || platform;
}

function sourcePlatformClass(platform) {
  if (!platform) return "platform-default";
  const slug = (platform || "").toLowerCase().replace(/\s+/g, "_");
  return `platform-${slug}`;
}

function parseBulletWithCitations(text, sources, highlightedSource, onCitationHover) {
  if (!text || typeof text !== "string") return text;
  const parts = [];
  const re = /\[S(\d+)\]/g;
  let lastIndex = 0;
  let match;
  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", value: text.slice(lastIndex, match.index) });
    }
    const num = parseInt(match[0].replace(/\D/g, ""), 10);
    const source = sources && sources[num - 1];
    parts.push({
      type: "citation",
      num,
      source,
      label: match[0],
      active: highlightedSource === num,
    });
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push({ type: "text", value: text.slice(lastIndex) });
  }
  return parts.length ? parts : [{ type: "text", value: text }];
}

function BulletWithCitations({ bullet, sources, highlightedSource, onCitationHover }) {
  const parsed = parseBulletWithCitations(bullet, sources, highlightedSource, onCitationHover);
  return (
    <span className="bullet-content">
      {parsed.map((part, i) =>
        part.type === "text" ? (
          <span key={i}>{part.value}</span>
        ) : (
          <span
            key={i}
            className={`citation ${part.active ? "highlight" : ""}`}
            title={part.source ? part.source.title : part.label}
            onMouseEnter={() => onCitationHover(part.num)}
            onMouseLeave={() => onCitationHover(null)}
          >
            {part.label}
          </span>
        )
      )}
    </span>
  );
}

function AskFlow() {
  const [question, setQuestion] = useState("");
  const [sourcesType, setSourcesType] = useState("all");
  const [imageUrl, setImageUrl] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [highlightedSource, setHighlightedSource] = useState(null);

  const onImageFileChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) {
      setImageFile(null);
      setImagePreview(null);
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setImageUrl("");
  }, []);

  const clearImage = useCallback(() => {
    setImageFile(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    setImageUrl("");
  }, [imagePreview]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!question.trim()) return;
      setError(null);
      setResult(null);
      setLoading(true);
      try {
        let data;
        if (imageFile) {
          const formData = new FormData();
          formData.append("question", question.trim());
          formData.append("sources_type", sourcesType);
          formData.append("context_limit", "10");
          formData.append("debug", "false");
          formData.append("image", imageFile);
          data = await askWithUpload(formData);
        } else {
          data = await ask({
            question: question.trim(),
            image_url: imageUrl.trim() || null,
            sources_type: sourcesType,
            context_limit: 10,
          });
        }
        setResult(data);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || "Request failed");
      } finally {
        setLoading(false);
      }
    },
    [question, imageUrl, imageFile, sourcesType]
  );

  const sources = result?.sources || [];
  const bullets = result?.explanation || [];

  return (
    <form onSubmit={handleSubmit}>
      <div className="card">
        <h2 className="card-title">Ask with context</h2>
        <textarea
          className="textarea"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Paste your post/question here..."
          rows={4}
          disabled={loading}
        />
        <div className="select-wrap">
          <label htmlFor="sources-type">Sources to search</label>
          <select
            id="sources-type"
            className="select"
            value={sourcesType}
            onChange={(e) => setSourcesType(e.target.value)}
            disabled={loading}
          >
            <option value="all">All (vector DB + web + social + news)</option>
            <option value="social">Social only (Reddit, Twitter)</option>
            <option value="news">News only</option>
          </select>
        </div>
        <input
          type="url"
          className="input"
          value={imageUrl}
          onChange={(e) => {
            setImageUrl(e.target.value);
            if (e.target.value) {
              setImageFile(null);
              if (imagePreview) URL.revokeObjectURL(imagePreview);
              setImagePreview(null);
            }
          }}
          placeholder="Optional: direct image URL"
          disabled={loading}
          style={{ marginTop: "0.75rem" }}
        />
        <label className="file-label" style={{ marginTop: "0.6rem", display: "inline-flex" }}>
          <span className="file-label-text">Or upload image</span>
          <input
            type="file"
            accept="image/*"
            onChange={onImageFileChange}
            disabled={loading}
            className="file-input"
          />
        </label>
        {imagePreview && (
          <div className="image-preview-wrap">
            <img src={imagePreview} alt="Preview" className="image-preview" />
            <button type="button" onClick={clearImage} className="image-clear">Remove</button>
          </div>
        )}
        <p className="input-optional">Use a direct image URL or upload an image file.</p>
        <button type="submit" className="btn" disabled={loading || !question.trim()}>
          {loading ? (
            <>
              <span className="loading-spinner" style={{ width: 18, height: 18, margin: 0 }} />
              Processing…
            </>
          ) : (
            <>Ask</>
          )}
        </button>
      </div>

      {error && (
        <div className="error-box" role="alert">
          {error}
        </div>
      )}

      {loading && (
        <div className="card loading">
          <div className="loading-spinner" />
          <p className="loading-text">Searching context & generating answer…</p>
        </div>
      )}

      {result && !loading && (
        <div className="result">
          {result.context_note && (
            <div className="context-badge" title={result.context_note}>
              {result.context_note}
            </div>
          )}
          <p className="meta">
            {result.processing_time_ms != null &&
              `${(result.processing_time_ms / 1000).toFixed(2)}s`}
            {result.context_sources_used && (
              <>
                {" · "}
                {result.context_sources_used.vector_db && "Vector DB "}
                {result.context_sources_used.web_available && "Web "}
                {result.context_sources_used.external && "External"}
              </>
            )}
          </p>
          <ul className="bullets">
            {bullets.map((b, i) => (
              <li key={i} className="bullet">
                <BulletWithCitations
                  bullet={b}
                  sources={sources}
                  highlightedSource={highlightedSource}
                  onCitationHover={setHighlightedSource}
                />
              </li>
            ))}
          </ul>
          {result.image_analysis && (
            <div className="card" style={{ marginTop: "1rem" }}>
              <h2 className="card-title">Image analysis</h2>
              <p style={{ margin: 0, fontSize: "0.95rem" }}>{result.image_analysis}</p>
            </div>
          )}
          {sources.length > 0 && (
            <div className="card" style={{ marginTop: "1rem" }}>
              <h2 className="card-title">Sources</h2>
              <div className="sources-grid">
                {sources.map((src, i) => (
                  <div
                    key={i}
                    className={`source-card ${sourcePlatformClass(src.platform)} ${highlightedSource === i + 1 ? "highlight" : ""}`}
                    onMouseEnter={() => setHighlightedSource(i + 1)}
                    onMouseLeave={() => setHighlightedSource(null)}
                  >
                    <span className="platform-tag">[{i + 1}] {sourcePlatformLabel(src.platform)}</span>
                    <h3 className="title">{src.title}</h3>
                    <p className="context">{src.context}</p>
                    {src.url && src.platform !== "vector_db" && (
                      <a href={src.url} target="_blank" rel="noopener noreferrer">
                        View source
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <h1 className="logo">Contextual Post Explainer</h1>
        <p className="subtitle">One endpoint: text + sources filter + image URL/upload</p>
      </header>
      <AskFlow />
    </div>
  );
}
