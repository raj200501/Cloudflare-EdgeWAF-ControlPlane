import { Link, Outlet } from 'react-router-dom';

const nav = [
  ['/', 'Overview'],
  ['/attack-map', 'Live Attack Map'],
  ['/events', 'Events Explorer'],
  ['/waf', 'WAF Rulesets'],
  ['/rate', 'Rate Limiting'],
  ['/geo', 'Geo Policy'],
  ['/bot', 'Bot Management'],
  ['/deployments', 'Deployments'],
  ['/analytics', 'Analytics'],
  ['/runbooks', 'Runbooks'],
];

export function AppShell() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <h1>IronShield</h1>
        {nav.map(([to, label]) => <Link key={to} to={to}>{label}</Link>)}
      </aside>
      <main className="content">
        <header className="header">Edge Security Control Plane</header>
        <Outlet />
      </main>
    </div>
  );
}
