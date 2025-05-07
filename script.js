console.log("GenesisOS initialized");
document.addEventListener('DOMContentLoaded', () => {
  // Add interactive logic here
});
const { execSync } = require('child_process');
const fs = require('fs');

function run(cmd) {
  console.log(`Running: ${cmd}`);
  try { execSync(cmd, { stdio: 'inherit' }); } catch (err) { console.error(err.message); }
}

function cleanGit() {
  run('git fetch --all');
  run('git checkout main');
  run('git reset --hard origin/main');
  run('git clean -fd');
  run('git pull origin main');
}

function fixFileNames() {
  const files = execSync('git ls-files').toString().split('\n');
  files.forEach(file => {
    if (/[ "$'`]/.test(file)) {
      const safeName = file.replace(/ /g, '_').replace(/["'$`]/g, '');
      fs.renameSync(file, safeName);
      run(`git mv "${file}" "${safeName}"`);
      console.log(`Renamed ${file} → ${safeName}`);
    }
  });
}

function checkSyntax() {
  run('npx eslint . || true');
  run('npx prettier --check . || true');
}

function prepareCommit() {
  run('git add .');
  run('git commit -m "Auto AI fix (Node.js)" || true');
  run('git push origin main');
}

cleanGit();
fixFileNames();
checkSyntax();
prepareCommit();
console.log('✅ Auto-fix Node.js script finished. Ready for rerun!');
