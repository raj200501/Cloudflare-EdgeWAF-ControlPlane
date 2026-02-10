import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AttackMapPage } from './pages/AttackMapPage';
import { BotPage } from './pages/BotPage';
import { DeploymentsPage } from './pages/DeploymentsPage';
import { EventsPage } from './pages/EventsPage';
import { GeoPage } from './pages/GeoPage';
import { OverviewPage } from './pages/OverviewPage';
import { RatePage } from './pages/RatePage';
import { RunbooksPage } from './pages/RunbooksPage';
import { WafPage } from './pages/WafPage';

export function App() {
  return (
    <Routes>
      <Route path='/' element={<AppShell />}>
        <Route index element={<OverviewPage />} />
        <Route path='attack-map' element={<AttackMapPage />} />
        <Route path='events' element={<EventsPage />} />
        <Route path='waf' element={<WafPage />} />
        <Route path='rate' element={<RatePage />} />
        <Route path='geo' element={<GeoPage />} />
        <Route path='bot' element={<BotPage />} />
        <Route path='deployments' element={<DeploymentsPage />} />
        <Route path='analytics' element={<AnalyticsPage />} />
        <Route path='runbooks' element={<RunbooksPage />} />
      </Route>
      <Route path='*' element={<Navigate to='/' />} />
    </Routes>
  );
}
