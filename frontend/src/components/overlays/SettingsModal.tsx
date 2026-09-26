import { useState } from 'react';
import { ChevronRight, Trash2 } from 'lucide-react';
import { Modal } from './Modal';
import { PrivacyPolicyView } from './PrivacyPolicyView';
import { clearConversations, useConversations } from '../../lib/storage';

export function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const conversations = useConversations();
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  const handleClose = () => {
    setShowPrivacy(false);
    setConfirmClear(false);
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title={showPrivacy ? '' : 'Settings'} width="sm">
      {showPrivacy ? (
        <PrivacyPolicyView onBack={() => setShowPrivacy(false)} />
      ) : (
        <div className="pl-settings-list">
          <button className="pl-settings-row pl-settings-link-row" onClick={() => setShowPrivacy(true)}>
            <div><strong>Privacy Policy</strong><p>How PrivacyLens handles your data.</p></div>
            <ChevronRight size={17} aria-hidden="true" />
          </button>

          <div className="pl-settings-row">
            <div>
              <strong>Clear recent analyses</strong>
              <p>{conversations.length} saved {conversations.length === 1 ? 'analysis' : 'analyses'} are stored on this device.</p>
            </div>
            <button className="secondary" disabled={!conversations.length} onClick={() => setConfirmClear(true)}>
              <Trash2 size={15} aria-hidden="true" /> Clear
            </button>
          </div>

          {confirmClear && (
            <div className="pl-settings-clear-confirm" role="alertdialog" aria-label="Clear recent analyses">
              <p><strong>Clear all recent analyses?</strong></p>
              <p>This removes the local analysis list from this device and cannot be undone.</p>
              <div>
                <button className="secondary" onClick={() => setConfirmClear(false)}>Cancel</button>
                <button className="primary" onClick={() => { clearConversations(); setConfirmClear(false); }}>Clear analyses</button>
              </div>
            </div>
          )}

          <div className="pl-settings-row">
            <div>
              <strong>About</strong>
              <p>PrivacyLens AI · Version 0.1.0</p>
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
