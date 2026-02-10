const fs = require('fs');
const path = require('path');

const app = fs.readFileSync(path.join(__dirname, '..', 'src', 'app.js'), 'utf8');
const requiredRoutes = [
  '/attack-map', '/events', '/waf', '/rate', '/geo', '/bot', '/deployments', '/analytics', '/runbooks'
];
for (const route of requiredRoutes) {
  if (!app.includes(route)) {
    console.error(`missing route ${route}`);
    process.exit(1);
  }
}
if (!app.includes('/ws/events')) {
  console.error('websocket subscription missing');
  process.exit(1);
}
if (!app.includes('/api/deployments/compile')) {
  console.error('deployment API usage missing');
  process.exit(1);
}
console.log('Dashboard tests passed.');
