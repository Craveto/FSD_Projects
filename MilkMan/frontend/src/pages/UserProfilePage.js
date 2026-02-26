import React, { useState } from 'react';
import '../styles/UserModules.css';

function UserProfilePage({ authUser }) {
  const [prefs, setPrefs] = useState(() => {
    const raw = window.localStorage.getItem('mm_user_prefs');
    return raw ? JSON.parse(raw) : {
      email_updates: true,
      sms_alerts: true,
      language: 'en',
    };
  });

  const savePreferences = () => {
    window.localStorage.setItem('mm_user_prefs', JSON.stringify(prefs));
  };

  return (
    <div className="user-module">
      <header className="user-module-header">
        <h1>Profile & Preferences</h1>
        <p>Manage your account identity and communication settings.</p>
      </header>

      <div className="module-card">
        <h3>{authUser?.first_name} {authUser?.last_name}</h3>
        <div className="module-meta">{authUser?.email}</div>
        <div className="module-meta">Role: {authUser?.role}</div>
      </div>

      <form className="module-form" onSubmit={(event) => {
        event.preventDefault();
        savePreferences();
      }}>
        <label>
          Language
          <select value={prefs.language} onChange={(event) => setPrefs({ ...prefs, language: event.target.value })}>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
        </label>
        <label>
          <input type="checkbox" checked={prefs.email_updates} onChange={(event) => setPrefs({ ...prefs, email_updates: event.target.checked })} />
          Email Updates
        </label>
        <label>
          <input type="checkbox" checked={prefs.sms_alerts} onChange={(event) => setPrefs({ ...prefs, sms_alerts: event.target.checked })} />
          SMS Alerts
        </label>
        <div className="module-actions">
          <button type="submit">Save Preferences</button>
        </div>
      </form>
    </div>
  );
}

export default UserProfilePage;
