import { useState } from 'react';
import { compileDeployment } from '../lib/api';

export function DeploymentsPage(){ const [snap, setSnap] = useState<any>(); return <div><h2>Deployments</h2><button onClick={async()=>setSnap(await compileDeployment())}>Compile Snapshot</button>{snap && <pre>{JSON.stringify(snap,null,2)}</pre>}</div>; }
