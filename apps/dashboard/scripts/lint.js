const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', 'src');
const files = fs.readdirSync(root).filter((f) => f.endsWith('.js'));
let failed = false;
for (const file of files) {
  const content = fs.readFileSync(path.join(root, file), 'utf8');
  if (content.includes('TODO')) {
    failed = true;
    console.error(`TODO found in ${file}`);
  }
}
if (failed) process.exit(1);
console.log('Static lint checks passed.');
