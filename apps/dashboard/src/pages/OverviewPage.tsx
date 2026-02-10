import { useEffect, useMemo, useState } from 'react';
import { fetchEvents, EventItem } from '../lib/api';
import { DataTable } from '../components/DataTable';

export function OverviewPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  useEffect(() => { fetchEvents(100).then(setEvents); }, []);
  const blocked = useMemo(() => events.filter((e) => e.decision === 'block').length, [events]);
  return <div><h2>Overview</h2><div className='kpi'><div>Events {events.length}</div><div>Blocked {blocked}</div></div><DataTable rows={events.slice(0,8)} /></div>;
}
