import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  const [apiStatus, setApiStatus] = useState('Checking…');
  const [dbStatus, setDbStatus] = useState('Checking…');

  useEffect(() => {
    const controller = new AbortController();
    async function check(path: string, update: (value: string) => void) {
      try {
        const response = await fetch(path, { signal: controller.signal });
        const data = await response.json();
        update(response.ok && ['ok', 'ready'].includes(data.status) ? 'Connected' : 'Unavailable');
      } catch {
        if (!controller.signal.aborted) update('Offline');
      }
    }
    void check('/api/health', setApiStatus);
    void check('/api/ready', setDbStatus);
    return () => controller.abort();
  }, []);

  return <main>
    <header><a className="brand" href="/">◈ SupportOps</a><span className="badge">Synthetic sandbox</span></header>
    <section className="intro"><p className="eyebrow">INVESTIGATION WORKSPACE</p><h1>Find the evidence.<br />Make the right call.</h1><p>Investigate support tickets, review the findings, and approve a specific fix.</p></section>
    <section className="status" aria-label="Service status" aria-live="polite">
      <div><span>API</span><strong>{apiStatus}</strong></div>
      <div><span>Postgres</span><strong>{dbStatus}</strong></div>
      <div><span>Agent runtime</span><strong>Not connected yet</strong></div>
    </section>
    <div className="workspace">
      <section className="panel"><p className="eyebrow">01 / TICKET</p><h2>Your investigation starts here</h2><p>No tickets have been seeded yet. The first scenario will investigate a paid upgrade that still shows the Free plan.</p><div className="example"><span>EXAMPLE CUSTOMER REPORT</span><blockquote>“I upgraded to Pro yesterday, but my account still shows the free plan.”</blockquote></div></section>
      <section className="panel"><p className="eyebrow">02 / EVIDENCE & ACTION</p><h2>Ready for the first trace</h2><p>Tool results and supporting records will appear here when investigations are connected.</p><div className="notice">Changes require approval. No mutation tools are enabled in this foundation.</div></section>
    </div>
    <footer>Development foundation · All future demo records are synthetic.</footer>
  </main>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
