import type { ReactNode } from 'react';

export function TextButton({ children, onClick, label }: { children: ReactNode; onClick: () => void; label?: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      style={{ background: 'none', border: 0, padding: 0, font: 'inherit', color: 'var(--accent-strong)', textDecoration: 'underline', cursor: 'pointer' }}
    >
      {children}
    </button>
  );
}
