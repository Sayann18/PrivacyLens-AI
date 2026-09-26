import { CheckCircle2, FileText, Sparkles, Upload } from 'lucide-react';
import { Modal } from './Modal';

const STEPS = [
  { n: '01', title: 'Add your document', text: 'Upload a PDF, DOCX, TXT, spreadsheet, presentation, image, or paste text.', icon: Upload },
  { n: '02', title: 'PrivacyLens analyzes it', text: 'PrivacyLens AI reviews the document and identifies important privacy-related terms, risks, and information.', icon: Sparkles },
  { n: '03', title: 'Understand the results', text: 'View the analysis in a simple, readable format \u2014 right in the conversation.', icon: FileText },
  { n: '04', title: 'Make better decisions', text: 'Understand what matters without having to read complicated legal language.', icon: CheckCircle2 }
];

export function HowItWorksModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose} title="How PrivacyLens Works" width="sm">
      <div className="pl-how-list">
        {STEPS.map(step => (
          <div className="pl-how-row" key={step.n}>
            <span className="pl-how-num" aria-hidden="true">{step.n}</span>
            <div className="pl-how-icon"><step.icon size={16} aria-hidden="true" /></div>
            <div>
              <strong>{step.title}</strong>
              <p>{step.text}</p>
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
}
