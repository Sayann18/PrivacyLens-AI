import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, FileText, Sparkles, Upload } from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageIntro } from '../components/ui/Panels';

const STEPS = [
  { n: '01', title: 'Add Your Document', text: 'Upload a PDF, DOCX, TXT, spreadsheet, presentation, image, or paste text.', icon: Upload },
  { n: '02', title: 'AI Analysis', text: 'PrivacyLens AI analyzes the document and identifies important privacy-related terms, risks, and information.', icon: Sparkles },
  { n: '03', title: 'Understand the Results', text: 'View the analysis in a simple, readable format.', icon: FileText },
  { n: '04', title: 'Make Better Decisions', text: 'Understand what matters without having to read complicated legal language.', icon: CheckCircle2 }
];

export function HowItWorksPage() {
  return (
    <AppShell title="How It Works">
      <PageIntro
        eyebrow="GUIDE"
        title="How It Works"
        text="Understand your privacy policies in a few simple steps."
        action={<Link className="primary" to="/">Try it now <ArrowRight size={16} aria-hidden="true" /></Link>}
      />
      <section className="how-steps">
        {STEPS.map(step => (
          <article className="panel how-step" key={step.n}>
            <span className="how-step-num" aria-hidden="true">{step.n}</span>
            <div className="how-step-icon"><step.icon size={20} aria-hidden="true" /></div>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </article>
        ))}
      </section>
    </AppShell>
  );
}
