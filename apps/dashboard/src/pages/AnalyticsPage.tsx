import { useEffect, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { fetchEvents } from '../lib/api';

export function AnalyticsPage(){
  const [series,setSeries]=useState<{t:number;lat:number}[]>([]);
  useEffect(()=>{fetchEvents(60).then((items)=>setSeries(items.map((e,i)=>({t:i,lat:e.latency_ms})).reverse()));},[]);
  return <div><h2>Analytics</h2><div style={{height:280}}><ResponsiveContainer><LineChart data={series}><XAxis dataKey='t'/><YAxis/><Line dataKey='lat' stroke='#f97316' /></LineChart></ResponsiveContainer></div></div>;
}
