import React from 'react';

export function PageIntro({ eyebrow, title, text, action }: { eyebrow: string; title: string; text: string; action?: React.ReactNode }) {
  return (
    <section className="page-intro">
      <div>
        <small className="eyebrow">{eyebrow}</small>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      {action}
    </section>
  );
}

export function Score({ name, value, icon: Icon }: { name: string; value: number; icon: React.ElementType }) {
  return (
    <article className="score-card">
      <div className="score-icon"><Icon size={19} aria-hidden="true" /></div>
      <small>{name}</small>
      <strong>{value}<em>/100</em></strong>
      <div className="meter" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
        <i style={{ width: `${value}%` }} />
      </div>
    </article>
  );
}

export function StatCard({ name, value, icon: Icon }: { name: string; value: number | string; icon: React.ElementType }) {
  return (
    <article className="score-card stat-card">
      <div className="score-icon"><Icon size={19} aria-hidden="true" /></div>
      <small>{name}</small>
      <strong>{value}</strong>
    </article>
  );
}
