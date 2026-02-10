import { useEffect, useState } from 'react';
import { DataTable } from '../components/DataTable';
import { fetchEvents, EventItem } from '../lib/api';

export function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  useEffect(() => { fetchEvents(300).then(setEvents); }, []);
  return <div><h2>Events Explorer</h2><DataTable rows={events} /></div>;
}
