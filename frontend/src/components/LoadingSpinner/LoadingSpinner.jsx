import React from "react";

const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center min-h-full">
      <div className="w-16 h-16 border-t-4 border-gold border-solid rounded-full animate-spin"></div>
    </div>
  );
};

export default LoadingSpinner;