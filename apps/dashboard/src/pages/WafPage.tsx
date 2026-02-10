import { useEffect, useState } from 'react';
import { createWafRule, fetchWafPolicies } from '../lib/api';
import { DataTable } from '../components/DataTable';

export function WafPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [pattern, setPattern] = useState('select');
  const refresh = () => fetchWafPolicies().then((d) => setRows(d.items || []));
  useEffect(refresh, []);
  return <div><h2>WAF Rulesets</h2><button onClick={async () => { await createWafRule({ field:'query', operator:'contains', pattern, reason:'custom', priority:2 }); refresh(); }}>Add Rule</button><input value={pattern} onChange={(e)=>setPattern(e.target.value)} /><DataTable rows={rows} /></div>;
}
