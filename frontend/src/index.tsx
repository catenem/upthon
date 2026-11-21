import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { AlertProvider, Alerts } from './components/Alerts';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <AlertProvider>
      {}
      <Alerts />
      <App />
    </AlertProvider>
  </React.StrictMode>
);