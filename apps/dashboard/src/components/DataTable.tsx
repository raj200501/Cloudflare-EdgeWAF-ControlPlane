import { ReactNode, useMemo, useState } from 'react';

type Row = Record<string, ReactNode | string | number>;

export function DataTable({ rows }: { rows: Row[] }) {
  const [query, setQuery] = useState('');
  const keys = rows.length ? Object.keys(rows[0]) : [];
  const filtered = useMemo(
    () => rows.filter((r) => JSON.stringify(r).toLowerCase().includes(query.toLowerCase())),
    [rows, query]
  );
  return (
    <div className="panel">
      <input placeholder="search" value={query} onChange={(e) => setQuery(e.target.value)} />
      <table>
        <thead><tr>{keys.map((k) => <th key={k}>{k}</th>)}</tr></thead>
        <tbody>
          {filtered.map((r, idx) => (
            <tr key={idx}>{keys.map((k) => <td key={k}>{r[k]}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
