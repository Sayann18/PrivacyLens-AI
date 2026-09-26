import { useEffect } from 'react';
import { AppShell } from '../components/layout/AppShell';
import { PageIntro } from '../components/ui/Panels';
import { useSettings } from '../lib/storage';

export function SettingsPage() {
  const [settings, updateSettings] = useSettings();
  useEffect(() => { document.documentElement.dataset.theme = settings.theme; }, [settings.theme]);

  return (
    <AppShell title="Settings">
      <PageIntro eyebrow="PREFERENCES" title="Make PrivacyLens yours." text="Configure your workspace without exposing any secrets." />
      <section className="settings panel">
        <div>
          <div>
            <h3>General</h3>
            <strong>Display name</strong>
            <p>Shown on your workspace avatar and sidebar.</p>
          </div>
          <input
            className="settings-input"
            value={settings.displayName}
            onChange={(event) => updateSettings({ displayName: event.target.value || 'Security workspace' })}
            aria-label="Display name"
            maxLength={24}
          />
        </div>
        <div>
          <div>
            <h3>Appearance</h3>
            <strong>Dark mode</strong>
            <p>Use the theme that works best for you.</p>
          </div>
          <label className="switch">
            <input
              type="checkbox"
              checked={settings.theme === 'dark'}
              onChange={(event) => updateSettings({ theme: event.target.checked ? 'dark' : 'light' })}
              aria-label="Toggle dark mode"
            />
            <span />
          </label>
        </div>
        <div>
          <div>
            <h3>Privacy</h3>
            <strong>Data handling</strong>
            <p>Documents you analyze are processed to generate your report and are stored only on this device, in your browser's local storage.</p>
          </div>
        </div>
        <div>
          <div>
            <h3>About</h3>
            <strong>PrivacyLens AI</strong>
            <p>Version 1.0 Local privacy analysis</p>
          </div>
        </div>
      </section>
    </AppShell>
  );
}
