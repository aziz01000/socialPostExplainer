import React, { useState, useCallback } from "react";
import { explainPost, socialQA } from "./api";
import "./App.css";

const MODES = { explain: "explain", qa: "qa" };

function sourcePlatformLabel(platform) {
  if (!platform) return "source";
  if (platform === "vector_db") return "Vector DB";
  return platform;
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

function ExplainFlow({ onResult }) {
  const [post, setPost] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [highlightedSource, setHighlightedSource] = useState(null);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!post.trim()) return;
      setError(null);
      setResult(null);
      setLoading(true);
      try {
        const data = await explainPost({
          post_content: post.trim(),
          image_url: imageUrl.trim() || null,
          context_limit: 10,
        });
        setResult(data);
        onResult?.();
      } catch (err) {
        setError(err.response?.data?.detail || err.message || "Request failed");
      } finally {
        setLoading(false);
      }
    },
    [post, imageUrl, onResult]
  );

  const sources = result?.sources || [];
  const bullets = result?.explanation || [];

  return (
    <form onSubmit={handleSubmit}>
      <div className="card">
        <h2 className="card-title">Paste a post</h2>
        <textarea
          className="textarea"
          value={post}
          onChange={(e) => setPost(e.target.value)}
          placeholder="e.g. The Ralph Wiggum technique is undefeated. Just bash-loop it until it works."
          rows={4}
          disabled={loading}
        />
        <input
          type="url"
          className="input"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          placeholder="Optional: image URL"
          disabled={loading}
          style={{ marginTop: "0.75rem" }}
        />
        <p className="input-optional">Optional image URL for vision context</p>
        <button type="submit" className="btn" disabled={loading || !post.trim()}>
          {loading ? (
            <>
              <span className="loading-spinner" style={{ width: 18, height: 18, margin: 0 }} />
              Explaining…
            </>
          ) : (
            <>Explain this post</>
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
          <p className="loading-text">Searching context & generating explanation…</p>
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
                    className={`source-card ${highlightedSource === i + 1 ? "highlight" : ""}`}
                  >
                    <span className="platform">[{i + 1}] {sourcePlatformLabel(src.platform)}</span>
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

function QAFlow({ onResult }) {
  const [question, setQuestion] = useState("");
  const [sourcesType, setSourcesType] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [highlightedSource, setHighlightedSource] = useState(null);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!question.trim()) return;
      setError(null);
      setResult(null);
      setLoading(true);
      try {
        const data = await socialQA({
          question: question.trim(),
          sources_type: sourcesType,
        });
        setResult(data);
        onResult?.();
      } catch (err) {
        setError(err.response?.data?.detail || err.message || "Request failed");
      } finally {
        setLoading(false);
      }
    },
    [question, sourcesType, onResult]
  );

  const sources = result?.sources || [];
  const answer = result?.answer;
  const summary = answer?.summary ?? "";
  const breakdown = result?.source_breakdown;

  return (
    <form onSubmit={handleSubmit}>
      <div className="card">
        <h2 className="card-title">Ask a question</h2>
        <textarea
          className="textarea"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What are people saying about the Ralph Wiggum technique?"
          rows={3}
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
            <option value="all">All (docs + web + social + news)</option>
            <option value="social">Social only (Reddit, Twitter)</option>
            <option value="news">News only</option>
          </select>
        </div>
        <button type="submit" className="btn" disabled={loading || question.trim().length < 3}>
          {loading ? (
            <>
              <span className="loading-spinner" style={{ width: 18, height: 18, margin: 0 }} />
              Searching…
            </>
          ) : (
            <>Get answer</>
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
          <p className="loading-text">Searching sources & synthesizing answer…</p>
        </div>
      )}

      {result && !loading && (
        <div className="result">
          <p className="meta">
            {result.processing_time_ms != null &&
              `${(result.processing_time_ms / 1000).toFixed(2)}s`}
            {breakdown?.combined_total != null && ` · ${breakdown.combined_total} sources`}
          </p>
          {breakdown?.platforms && Object.keys(breakdown.platforms).length > 0 && (
            <div className="breakdown">
              {Object.entries(breakdown.platforms).map(([platform, count]) => (
                <span key={platform} className="breakdown-pill">
                  {platform}: {count}
                </span>
              ))}
            </div>
          )}
          <div className="answer-summary">
            {summary.split("\n").map((para, i) => (
              <p key={i} style={{ margin: i > 0 ? "0.75rem 0 0" : 0 }}>
                {para}
              </p>
            ))}
          </div>
          {sources.length > 0 && (
            <div className="card" style={{ marginTop: "1rem" }}>
              <h2 className="card-title">Sources</h2>
              <div className="sources-grid">
                {sources.map((src, i) => (
                  <div
                    key={i}
                    className={`source-card ${highlightedSource === i + 1 ? "highlight" : ""}`}
                  >
                    <span className="platform">{sourcePlatformLabel(src.platform)}</span>
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
  const [mode, setMode] = useState(MODES.explain);

  return (
    <div className="app">
      <header className="header">
        <h1 className="logo">Contextual Post Explainer</h1>
        <p className="subtitle">Explain social posts with context & citations</p>
      </header>

      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={mode === MODES.explain}
          className={`tab ${mode === MODES.explain ? "active" : ""}`}
          onClick={() => setMode(MODES.explain)}
        >
          Explain a post
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === MODES.qa}
          className={`tab ${mode === MODES.qa ? "active" : ""}`}
          onClick={() => setMode(MODES.qa)}
        >
          Social Q&A
        </button>
      </div>

      {mode === MODES.explain && <ExplainFlow />}
      {mode === MODES.qa && <QAFlow />}
    </div>
  );
}
