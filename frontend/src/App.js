import React, { useState, useEffect } from "react";
import PostInput from "./components/PostInput";
import ExplanationView from "./components/ExplanationView";
import SourceList from "./components/SourceList";
import { explainPost, healthCheck } from "./api";
import "./App.css";

function App() {
  const [explanation, setExplanation] = useState("");
  const [sources, setSources] = useState([]);
  const [imageAnalysis, setImageAnalysis] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [backendHealthy, setBackendHealthy] = useState(false);

  useEffect(() => {
    // Check backend health on mount
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    const healthy = await healthCheck();
    setBackendHealthy(healthy);
    if (!healthy) {
      setError(
        "Backend service is not available. Please ensure the FastAPI server is running on http://localhost:8000"
      );
    }
  };

  const handleExplainPost = async (post, imageUrl) => {
    setIsLoading(true);
    setError("");
    setExplanation("");
    setSources([]);
    setImageAnalysis("");

    try {
      const result = await explainPost(post, imageUrl);
      setExplanation(result.explanation);
      setSources(result.sources || []);
      setImageAnalysis(result.image_analysis || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Contextual Post Explainer</h1>
          <p>
            Understand social media posts with AI-powered explanations and
            citations
          </p>
          {!backendHealthy && (
            <div className="health-warning">
              <strong>⚠️ Backend Not Available</strong>
            </div>
          )}
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <PostInput onSubmit={handleExplainPost} isLoading={isLoading} />

          {error && <div className="error-banner">{error}</div>}

          {explanation && (
            <div className="results">
              <ExplanationView
                explanation={explanation}
                imageAnalysis={imageAnalysis}
              />
              <SourceList sources={sources} />
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Powered by LangGraph, FastAPI, and OpenAI | Observability with Arize
          Phoenix
        </p>
      </footer>
    </div>
  );
}

export default App;
