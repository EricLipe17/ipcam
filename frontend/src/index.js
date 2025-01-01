import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <App />
  // TODO: Figure out how to get strict mode working with react player!
  // <React.StrictMode>
  //   <App />
  // </React.StrictMode>
);
