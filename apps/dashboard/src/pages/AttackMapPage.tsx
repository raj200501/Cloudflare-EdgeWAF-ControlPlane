import { useEffect, useState } from 'react';
import { fetchEvents, EventItem } from '../lib/api';

const dc = { x: 650, y: 180 };
const points: Record<string, { x: number; y: number }> = { US: { x: 180, y: 170 }, DE: { x: 400, y: 130 }, BR: { x: 260, y: 280 }, IN: { x: 500, y: 180 }, Unknown: { x: 80, y: 60 } };

export function AttackMapPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  useEffect(() => { fetchEvents(100).then(setEvents); }, []);
  return <div><h2>Live Attack Map</h2><svg viewBox='0 0 800 400' className='map'>
    <rect width='800' height='400' fill='#111827' />
    {events.slice(0, 40).map((e) => { const p = points[e.country] ?? points.Unknown; return <line key={e.id} x1={p.x} y1={p.y} x2={dc.x} y2={dc.y} stroke={e.decision === 'block' ? '#f97316' : '#38bdf8'} strokeOpacity='0.6' />; })}
    <circle cx={dc.x} cy={dc.y} r='6' fill='#f97316' />
  </svg></div>;
}
