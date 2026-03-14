/**
 * ExplanationView Component - Display the generated explanation
 */

import React from "react";
import "./ExplanationView.css";

function ExplanationView({ explanation, imageAnalysis }) {
  return (
    <div className="explanation-container">
      <h2>Explanation</h2>

      {imageAnalysis && (
        <div className="image-analysis">
          <h3>Image Analysis:</h3>
          <p>{imageAnalysis}</p>
        </div>
      )}

      <div className="explanation-content">
        {explanation.split("\n").map((bullet, index) => {
          if (bullet.trim()) {
            return (
              <div key={index} className="explanation-bullet">
                {bullet}
              </div>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}

export default ExplanationView;
