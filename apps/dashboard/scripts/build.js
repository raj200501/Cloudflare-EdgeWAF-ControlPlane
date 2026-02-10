const fs = require('fs');
const path = require('path');

const src = path.join(__dirname, '..', 'src');
const dist = path.join(__dirname, '..', 'dist');

function copyRecursive(from, to) {
  const stat = fs.statSync(from);
  if (stat.isDirectory()) {
    fs.mkdirSync(to, { recursive: true });
    for (const item of fs.readdirSync(from)) {
      copyRecursive(path.join(from, item), path.join(to, item));
    }
  } else {
    fs.mkdirSync(path.dirname(to), { recursive: true });
    fs.copyFileSync(from, to);
  }
}

fs.rmSync(dist, { recursive: true, force: true });
copyRecursive(src, dist);
console.log('Built dashboard to dist/.');
