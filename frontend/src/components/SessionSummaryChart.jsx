import { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { EMOTION_META } from './emotionMeta.js';

const EMOTION_COLORS = {
  angry:   'var(--emotion-angry)',
  happy:   'var(--emotion-happy)',
  sad:     'var(--emotion-sad)',
  fear:    'var(--emotion-fear)',
  neutral: 'var(--emotion-neutral)',
};

// Recharts needs real hex/rgb, not CSS vars, for SVG fills
const EMOTION_COLORS_HEX = {
  angry:   '#d32f2f',
  happy:   '#e07b1a',
  sad:     '#1565c0',
  fear:    '#6a1b9a',
  neutral: '#455a64',
};

const EMOTION_ORDER = ['angry', 'happy', 'sad', 'fear', 'neutral'];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const { name, value } = payload[0];
    const meta = EMOTION_META[name];
    return (
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '8px 12px',
        fontSize: '0.8rem',
        boxShadow: 'var(--shadow-md)',
      }}>
        <strong>{meta?.emoji} {name}</strong>: {value} {value === 1 ? 'comment' : 'comments'}
      </div>
    );
  }
  return null;
};

export default function SessionSummaryChart({ history }) {
  const data = useMemo(() => {
    const counts = {};
    for (const item of history) {
      counts[item.emotion] = (counts[item.emotion] ?? 0) + 1;
    }
    return EMOTION_ORDER
      .filter(e => counts[e] > 0)
      .map(e => ({ name: e, value: counts[e] }));
  }, [history]);

  return (
    <div className="card">
      <div className="card__header">
        <span className="card__header-icon">🥧</span>
        <span className="card__header-label">Session Summary</span>
      </div>

      <div className="card__body">
        {history.length === 0 ? (
          <div className="history-empty" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: 8, opacity: 0.35 }}>📊</div>
            <p>Emotion distribution will appear here once you analyze comments.</p>
          </div>
        ) : (
          <div className="summary-chart-wrapper">
            <div style={{ width: '100%', height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={88}
                    paddingAngle={3}
                    dataKey="value"
                    animationBegin={0}
                    animationDuration={600}
                  >
                    {data.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={EMOTION_COLORS_HEX[entry.name] ?? '#aaa'}
                        stroke="var(--surface)"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Custom legend */}
            <div className="summary-legend">
              {data.map((entry) => (
                <div key={entry.name} className="legend-item">
                  <span
                    className="legend-dot"
                    style={{ background: EMOTION_COLORS_HEX[entry.name] }}
                  />
                  <span>
                    {EMOTION_META[entry.name]?.emoji} {entry.name} ({entry.value})
                  </span>
                </div>
              ))}
            </div>

            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              Total analyzed: <strong>{history.length}</strong> comment{history.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
