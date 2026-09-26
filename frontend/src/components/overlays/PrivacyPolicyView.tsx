import { ArrowLeft } from 'lucide-react';

export function PrivacyPolicyView({ onBack }: { onBack: () => void }) {
  return (
    <div className="pl-privacy-view">
      <button className="pl-modal-back" onClick={onBack}>
        <ArrowLeft size={15} aria-hidden="true" /> Back
      </button>
      <h2 className="pl-privacy-title">Privacy Policy</h2>
      <div className="pl-privacy-content">
        <p>PrivacyLens AI is built to help you understand other people's privacy policies — so it only makes sense that we're straightforward about our own.</p>
        <h4>What stays on your device</h4>
        <p>Your recent analyses, pinned conversations, renamed titles, and workspace settings are stored locally in your browser's storage. They are not uploaded to any account or shared with third parties, and they stay on this device unless you clear them yourself.</p>
        <h4>What gets sent for analysis</h4>
        <p>When you paste text, upload a document, or submit a URL, that content is sent to the PrivacyLens analysis service solely to generate your report. It is used only to produce the analysis you requested.</p>
        <h4>Your controls</h4>
        <p>You can delete individual analyses or clear your recent analysis list whenever you like. Removing an analysis removes it from this device.</p>
        <h4>Questions</h4>
        <p>If you have questions about how PrivacyLens handles your information, reach out through the support channel listed in the app.</p>
      </div>
    </div>
  );
}
