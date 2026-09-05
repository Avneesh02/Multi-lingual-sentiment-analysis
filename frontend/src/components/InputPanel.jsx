import { useState } from 'react';
import { API_BASE_URL } from '../config.js';

const TARGET_LANGS = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
  { code: 'mr', label: 'Marathi' },
  { code: 'bn', label: 'Bengali' },
  { code: 'ta', label: 'Tamil' },
  { code: 'te', label: 'Telugu' },
  { code: 'kn', label: 'Kannada' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'gu', label: 'Gujarati' },
];

export default function InputPanel({
  text, setText, loading, connected,
  apiError, samples, onAnalyze, onClear, onSampleSelect, onTranslated,
}) {
  const MAX_CHARS = 1000;
  const isDisabled = !text.trim() || loading || connected !== 'connected';
  const charWarn = text.length > MAX_CHARS * 0.85;

  const [translating, setTranslating] = useState(false);
  const [translation, setTranslation] = useState('');
  const [transError, setTransError] = useState('');
  const [targetLang, setTargetLang] = useState('en');

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!isDisabled) onAnalyze();
    }
  };

  // Clear translation whenever text changes
  const handleTextChange = (e) => {
    setText(e.target.value);
    setTranslation('');
    setTransError('');
  };

  const handleTranslate = async () => {
    if (!text.trim()) return;
    setTranslating(true);
    setTranslation('');
    setTransError('');
    try {
      const params = new URLSearchParams({ text: text.trim(), tl: targetLang });
      const res = await fetch(`${API_BASE_URL}/translate?${params}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Translation failed');
      setTranslation(data.translated);
      if (onTranslated) onTranslated(data.translated);
    } catch (err) {
      setTransError('Translation unavailable. Check internet connection.');
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="card">
      <div className="card__header">
        <span className="card__header-icon">✏️</span>
        <span className="card__header-label">Comment Input</span>
      </div>

      <div className="card__body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap-md)' }}>
        {/* Sample dropdown */}
        <div className="input-panel__row">
          <label className="input-panel__label" htmlFor="sample-select">
            Load Sample Comment
          </label>
          <select
            id="sample-select"
            className="input-panel__select"
            defaultValue=""
            onChange={(e) => {
              onSampleSelect(e.target.value);
              setTranslation(''); setTransError('');
              e.target.value = '';
            }}
          >
            <option value="" disabled>— select a language &amp; sample —</option>
            {samples.map((group) => (
              <optgroup key={group.code} label={`${group.lang} (${group.native})`}>
                {group.samples.map((s, i) => (
                  <option key={i} value={s}>{s.length > 72 ? s.slice(0, 72) + '…' : s}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div className="section-divider" />

        {/* Textarea */}
        <div className="input-panel__row">
          <label className="input-panel__label" htmlFor="comment-input">
            Enter Comment
          </label>
          <div className="textarea-wrapper">
            <textarea
              id="comment-input"
              className="input-panel__textarea"
              value={text}
              onChange={handleTextChange}
              onKeyDown={handleKeyDown}
              placeholder="Type or paste a comment in any of the 9 supported languages…"
              maxLength={MAX_CHARS}
              rows={6}
              aria-label="Comment text for emotion analysis"
            />
            <span className={`char-counter${charWarn ? ' char-counter--warn' : ''}`}>
              {text.length}/{MAX_CHARS}
            </span>
          </div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Tip: Press <kbd style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 3, padding: '1px 5px', fontSize: '0.68rem' }}>Ctrl+Enter</kbd> to analyze
          </span>
        </div>

        {/* Translate row: dropdown + button */}
        {text.trim() && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <select
              value={targetLang}
              onChange={(e) => { setTargetLang(e.target.value); setTranslation(''); }}
              style={{ flex: '0 0 auto', padding: '7px 10px', borderRadius: 6, border: '1.5px solid var(--border-strong)', fontSize: '0.8rem', color: 'var(--text-primary)', background: 'var(--surface)', cursor: 'pointer' }}
              aria-label="Target translation language"
            >
              {TARGET_LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
            <button className="btn-translate" style={{ flex: 1 }} onClick={handleTranslate} disabled={translating}>
              {translating
                ? <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Translating…</>
                : <><span aria-hidden="true">🌐</span> Translate Via Google Translate</>
              }
            </button>
          </div>
        )}

        {/* Inline translation result */}
        {translation && (
          <div className="translation-box">
            <span className="translation-box__label">English Translation</span>
            <p className="translation-box__text">{translation}</p>
          </div>
        )}
        {transError && (
          <p style={{ fontSize: '0.78rem', color: 'var(--error)' }}>{transError}</p>
        )}

        {/* Action row */}
        <div className="input-panel__actions">
          <button
            id="analyze-btn"
            className={`btn-analyze${loading ? ' btn-analyze--loading' : ''}`}
            onClick={onAnalyze}
            disabled={isDisabled}
            aria-busy={loading}
          >
            {loading ? (
              <><span className="spinner" aria-hidden="true" /> Analyzing…</>
            ) : (
              <><span aria-hidden="true">🔍</span> Analyze Emotion</>
            )}
          </button>

          {text && (
            <button id="clear-btn" className="btn-clear" onClick={() => { onClear(); setTranslation(''); setTransError(''); }} disabled={loading}>
              Clear
            </button>
          )}

          {connected === 'disconnected' && (
            <span className="offline-notice">
              ⚠️ Backend offline — start uvicorn and click Retry in the header.
            </span>
          )}
        </div>

        {/* API error */}
        {apiError && (
          <div className="error-banner" role="alert">
            <span aria-hidden="true">⚠️</span>
            <span>{apiError}</span>
          </div>
        )}
      </div>
    </div>
  );
}
