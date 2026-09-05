import { useEffect, useState, useRef } from 'react';
import { SAMPLE_COMMENTS } from './sampleComments.js';
import { API_BASE_URL } from './config.js';
import ConnectivityBadge from './components/ConnectivityBadge.jsx';
import InputPanel from './components/InputPanel.jsx';
import ResultCard from './components/ResultCard.jsx';
import SessionHistory from './components/SessionHistory.jsx';
import SessionSummaryChart from './components/SessionSummaryChart.jsx';
import BulkAnalysis from './components/BulkAnalysis.jsx';

export default function App() {
  // ── Connection state ──────────────────────────────────────
  const [connected, setConnected] = useState('checking'); // 'checking' | 'connected' | 'disconnected'

  // ── Input state ───────────────────────────────────────────
  const [text, setText] = useState('');
  const [translatedText, setTranslatedText] = useState(''); // set when user translates

  // ── Inference state ───────────────────────────────────────
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);   // last successful result
  const [apiError, setApiError] = useState(null);

  // ── Session history ───────────────────────────────────────
  const [history, setHistory] = useState([]);

  // ── Health check ──────────────────────────────────────────
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const data = await res.json();
        setConnected(data.model_loaded ? 'connected' : 'disconnected');
      } else {
        setConnected('disconnected');
      }
    } catch {
      setConnected('disconnected');
    }
  };

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 30_000);
    return () => clearInterval(id);
  }, []);

  // ── Analyze ───────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!text.trim() || loading || connected !== 'connected') return;
    setLoading(true);
    setApiError(null);

    try {
      // Use translated text if available (correct script for language detection)
      const textToAnalyze = translatedText.trim() || text.trim();
      const res = await fetch(`${API_BASE_URL}/emotion/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToAnalyze }),
      });

      const data = await res.json();

      if (!res.ok) {
        setApiError(data?.detail ?? `Request failed (HTTP ${res.status}).`);
        setLoading(false);
        return;
      }

      setResult(data);
      setHistory(prev => [
        {
          id: Date.now(),
          text: text.trim(),
          emotion: data.emotion,
          language: data.language,
          confidence: data.confidence,
          timestamp: new Date(),
        },
        ...prev,
      ]);
    } catch (err) {
      setApiError('Network error — could not reach the backend. Is uvicorn running?');
    } finally {
      setLoading(false);
    }
  };

  // ── Sample select ─────────────────────────────────────────
  const handleSampleSelect = (value) => {
    if (value) {
      setText(value);
      setTranslatedText('');
      setResult(null);
      setApiError(null);
    }
  };

  // ── Clear ─────────────────────────────────────────────────
  const handleClear = () => {
    setText('');
    setTranslatedText('');
    setResult(null);
    setApiError(null);
  };

  return (
    <div className="app-shell">
      {/* ── Header ────────────────────────────────────────── */}
      <header className="site-header">
        <div className="site-header__inner">
          <div className="site-header__brand">
            <div>
              <div className="site-header__title">
                e-Consultation Sentiment Analysis Dashboard
              </div>
              <div className="site-header__subtitle">
                Multilingual Emotion Classification · 9 Indian Languages + English
              </div>
            </div>
          </div>
          <ConnectivityBadge status={connected} onRetry={checkHealth} />
        </div>
      </header>

      {/* ── Main ──────────────────────────────────────────── */}
      <main className="main-content">
        <div className="dashboard-grid">
          {/* Left: Input */}
          <InputPanel
            text={text}
            setText={(v) => { setText(v); setTranslatedText(''); }}
            loading={loading}
            connected={connected}
            apiError={apiError}
            samples={SAMPLE_COMMENTS}
            onAnalyze={handleAnalyze}
            onClear={handleClear}
            onSampleSelect={handleSampleSelect}
            onTranslated={(t) => setTranslatedText(t)}
          />

          {/* Right: Result */}
          <ResultCard result={result} loading={loading} originalText={text} />
        </div>

        {/* Bottom row: history + summary */}
          <div className="bottom-row">
            <SessionHistory history={history} />
            <SessionSummaryChart history={history} />
          </div>

          {/* Bulk analysis section */}
          <BulkAnalysis connected={connected} />
      </main>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="site-footer">
        Built for <em>Sentiment Analysis E-Consultation Module</em> &nbsp;·&nbsp;
        Multilingual Emotion Analysis &nbsp;·&nbsp;
        9 Indian Languages · Powered by ai4bharat/indic-bert
      </footer>
    </div>
  );
}
