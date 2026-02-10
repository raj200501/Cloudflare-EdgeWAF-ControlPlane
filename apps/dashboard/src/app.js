const app = document.getElementById('app');

const state = {
  events: [],
  tab: 'Live Map',
  underAttack: false,
  denylist: ''
};

const tabs = ['Live Map', 'Threats', 'Requests', 'Config'];

const countryCoords = {
  US: [-98, 39],
  DE: [10, 51],
  FR: [2, 46],
  BR: [-51, -10],
  JP: [138, 36],
  IN: [78, 21],
  AU: [134, -25],
  CN: [104, 35],
  RU: [100, 60],
  GB: [-3, 55],
  NL: [5, 52],
  CA: [-106, 56],
  Unknown: [0, 0]
};
const datacenter = [-122.3, 37.8];

const apiBase = 'http://localhost:8080';

const render = () => {
  app.innerHTML = `
    <header>
      <div>
        <h1 style="color: var(--accent-red); margin: 0;">IronShield</h1>
        <p style="margin: 4px 0; color: #94a3b8;">Local edge proxy + WAF + live attack map</p>
      </div>
      <div style="letter-spacing: 2px; text-transform: uppercase; font-size: 12px; color: var(--accent-green);">
        Under Attack Mode: ${state.underAttack ? 'ON' : 'OFF'}
      </div>
    </header>
    <nav>
      ${tabs
        .map(
          (tab) =>
            `<button class="${state.tab === tab ? 'active' : ''}" data-tab="${tab}">${tab}</button>`
        )
        .join('')}
    </nav>
    <main>
      ${renderTab()}
    </main>
  `;

  document.querySelectorAll('nav button').forEach((button) => {
    button.addEventListener('click', () => {
      state.tab = button.dataset.tab;
      render();
      if (state.tab === 'Live Map') {
        drawMap();
      }
    });
  });

  if (state.tab === 'Config') {
    document.getElementById('toggle-attack').addEventListener('click', async () => {
      const next = !state.underAttack;
      await fetch(`${apiBase}/api/config/under_attack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: next })
      });
      state.underAttack = next;
      render();
    });
    document.getElementById('denylist').addEventListener('input', (event) => {
      state.denylist = event.target.value;
    });
    document.getElementById('update-denylist').addEventListener('click', async () => {
      const list = state.denylist
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean);
      await fetch(`${apiBase}/api/config/geo_denylist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ denylist: list })
      });
    });
  }

  if (state.tab === 'Live Map') {
    drawMap();
  }
};

const renderTab = () => {
  if (state.tab === 'Live Map') {
    return `
      <div class="panel">
        <h2>Live Attack Map</h2>
        <canvas id="map" width="900" height="450"></canvas>
      </div>
    `;
  }
  if (state.tab === 'Threats') {
    const counts = state.events.reduce((acc, event) => {
      acc[event.reason] = (acc[event.reason] || 0) + 1;
      return acc;
    }, {});
    const allowed = state.events.filter((event) => event.decision === 'allow').length;
    const blocked = state.events.filter((event) => event.decision === 'block').length;
    return `
      <div class="grid two">
        <div class="panel">
          <h2>Decisions</h2>
          <p>Allowed: ${allowed}</p>
          <p>Blocked: ${blocked}</p>
        </div>
        <div class="panel">
          <h2>Top Reasons</h2>
          <ul>
            ${Object.entries(counts)
              .map(([reason, count]) => `<li>${reason}: <span class="badge red">${count}</span></li>`)
              .join('')}
          </ul>
        </div>
      </div>
    `;
  }
  if (state.tab === 'Requests') {
    return `
      <div class="panel">
        <table class="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>IP</th>
              <th>Country</th>
              <th>Path</th>
              <th>Decision</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            ${state.events
              .slice(0, 20)
              .map(
                (event) => `
              <tr>
                <td>${new Date(event.ts * 1000).toLocaleTimeString()}</td>
                <td>${event.ip}</td>
                <td>${event.country}</td>
                <td>${event.path}</td>
                <td class="badge ${event.decision === 'block' ? 'red' : 'green'}">${event.decision}</td>
                <td>${event.reason}</td>
              </tr>
            `
              )
              .join('')}
          </tbody>
        </table>
      </div>
    `;
  }
  return `
    <div class="grid">
      <div class="panel">
        <h2>Under Attack Mode</h2>
        <p>Tighten rate limiting and enable stricter WAF group.</p>
        <button id="toggle-attack" class="primary">Toggle Under Attack</button>
      </div>
      <div class="panel">
        <h2>Geo Denylist</h2>
        <p>Comma-separated country codes.</p>
        <input id="denylist" placeholder="CN,RU" value="${state.denylist}" />
        <button id="update-denylist" class="secondary">Update Denylist</button>
      </div>
    </div>
  `;
};

const drawMap = () => {
  const canvas = document.getElementById('map');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const toXY = (lon, lat) => {
    const x = ((lon + 180) / 360) * canvas.width;
    const y = ((90 - lat) / 180) * canvas.height;
    return [x, y];
  };

  let tick = 0;
  const draw = () => {
    tick += 1;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#1e293b';
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    const [dcX, dcY] = toXY(datacenter[0], datacenter[1]);
    ctx.fillStyle = '#32ff6a';
    ctx.beginPath();
    ctx.arc(dcX, dcY, 6 + Math.sin(tick / 8) * 2, 0, Math.PI * 2);
    ctx.fill();

    state.events.slice(0, 60).forEach((event, index) => {
      const [lon, lat] = countryCoords[event.country] || countryCoords.Unknown;
      const [x, y] = toXY(lon, lat);
      ctx.strokeStyle = event.decision === 'block' ? '#ff3860' : '#32ff6a';
      ctx.globalAlpha = 1 - index / 70;
      ctx.beginPath();
      const controlX = (x + dcX) / 2;
      const controlY = (y + dcY) / 2 - 30 - (tick % 20);
      ctx.moveTo(x, y);
      ctx.quadraticCurveTo(controlX, controlY, dcX, dcY);
      ctx.stroke();
      ctx.globalAlpha = 1;
    });

    requestAnimationFrame(draw);
  };
  draw();
};

const connectWebSocket = () => {
  const ws = new WebSocket('ws://localhost:8080/ws/events');
  ws.onmessage = (message) => {
    const event = JSON.parse(message.data);
    state.events = [event, ...state.events].slice(0, 200);
    if (state.tab !== 'Live Map') {
      render();
    }
  };
  ws.onerror = () => {
    ws.close();
  };
};

const init = async () => {
  const response = await fetch(`${apiBase}/api/events/recent`);
  const data = await response.json();
  state.events = data.events || [];
  render();
  connectWebSocket();
};

init().catch(() => render());
