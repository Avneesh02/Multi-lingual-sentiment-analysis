// Maps emotion name → { emoji, color variable }
export const EMOTION_META = {
  angry:   { emoji: '😠', color: 'var(--emotion-angry)',   label: 'Angry' },
  happy:   { emoji: '😊', color: 'var(--emotion-happy)',   label: 'Happy' },
  sad:     { emoji: '😢', color: 'var(--emotion-sad)',     label: 'Sad' },
  fear:    { emoji: '😨', color: 'var(--emotion-fear)',    label: 'Fear' },
  neutral: { emoji: '😐', color: 'var(--emotion-neutral)', label: 'Neutral' },
};

// Maps language code → native script name
export const NATIVE_NAMES = {
  hi: 'हिंदी',
  mr: 'मराठी',
  bn: 'বাংলা',
  ta: 'தமிழ்',
  te: 'తెలుగు',
  kn: 'ಕನ್ನಡ',
  ml: 'മലയാളം',
  gu: 'ગુજરાતી',
  en: 'English',
};
