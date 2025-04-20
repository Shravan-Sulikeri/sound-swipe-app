import React from "react";
import '../components/styling/chunking.css';

const ChunkingProgress = ({ progress, totalLoaded, totalProcessed, isLoading }) => {
  if (!isLoading) return null;
  
  return (
    <div className="chunking-progress">
      <div className="progress-bar-container">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="progress-text">
        {totalLoaded > 0 ? (
          <span>Loaded {totalLoaded} of {totalProcessed || '?'} tracks ({progress}%)</span>
        ) : (
          <span>Preparing tracks...</span>
        )}
      </div>
    </div>
  );
};

export default ChunkingProgress;