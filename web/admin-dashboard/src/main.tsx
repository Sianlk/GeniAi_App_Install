import React from 'react';
import ReactDOM from 'react-dom/client';

const SUPER_ADMIN_EMAIL = 'hosturserver@gmail.com';

function App() {
  return (
    <main style={{ fontFamily: 'Manrope, sans-serif', padding: 24, background: '#030712', color: '#f8fafc', minHeight: '100vh' }}>
      <h1>Hostur Super Admin Console</h1>
      <p>Authorized super admin: {SUPER_ADMIN_EMAIL}</p>
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 12, marginTop: 18 }}>
        <article style={{ background: '#111827', borderRadius: 12, padding: 14 }}>
          <h3>Global User Control</h3>
          <p>Manage users, plans, app memberships, and role escalations.</p>
        </article>
        <article style={{ background: '#111827', borderRadius: 12, padding: 14 }}>
          <h3>Feature Injection</h3>
          <p>Inject per-user or per-app feature overrides from a controlled admin channel.</p>
        </article>
        <article style={{ background: '#111827', borderRadius: 12, padding: 14 }}>
          <h3>AI Workforce Feed</h3>
          <p>Review autonomous improvement suggestions and approve deployment plans.</p>
        </article>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
