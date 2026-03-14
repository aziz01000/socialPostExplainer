/**
 * SourceList Component - Display source citations
 */

import React from "react";
import "./SourceList.css";

function SourceList({ sources }) {
  return (
    <div className="sources-container">
      <h2>Sources</h2>

      {sources.length === 0 ? (
        <p className="no-sources">No sources found</p>
      ) : (
        <div className="sources-list">
          {sources.map((source, index) => (
            <div key={index} className="source-item">
              <div className="source-number">[Source {index + 1}]</div>
              <div className="source-title">
                {source.title || "Untitled Source"}
              </div>
              {source.context && (
                <div className="source-context">{source.context}</div>
              )}
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="source-link"
              >
                {source.url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SourceList;
