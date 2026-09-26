import { useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ConversationPage } from './components/conversation/ConversationPage';
import { readSettings } from './lib/storage';
import './styles.css';

export default function Root() {
  useEffect(() => {
    document.documentElement.dataset.theme = readSettings().theme;
  }, []);
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<ConversationPage />} />
          <Route path="/c/:id" element={<ConversationPage />} />
          <Route path="*" element={<ConversationPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
