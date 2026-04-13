import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const templateDir = path.join(root, 'mobile', 'template-autonomous-trading-coach');
const appsDir = path.join(root, 'mobile', 'apps');

const apps = [
  'sianlk-core',
  'geniai-persona-studio',
  'ai-aesthetics-lab',
  'ai-business-brain',
  'aiblty-coach',
  'aibltycode-studio',
  'buildquote-pro',
  'comppropdata-intelligence',
  'terminalai-ops',
  'gitgit-copilot',
  'autonomous-trading-coach'
];

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

for (const app of apps) {
  const target = path.join(appsDir, app);
  if (fs.existsSync(target)) {
    console.log(`skip: ${app} already exists`);
    continue;
  }
  copyDir(templateDir, target);
  const appJsonPath = path.join(target, 'app.json');
  const packageJsonPath = path.join(target, 'package.json');

  const appJson = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));
  appJson.expo.name = app;
  appJson.expo.slug = app;
  appJson.expo.extra = { ...(appJson.expo.extra || {}), appId: app };
  fs.writeFileSync(appJsonPath, JSON.stringify(appJson, null, 2));

  const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  pkg.name = `@unified/${app}`;
  fs.writeFileSync(packageJsonPath, JSON.stringify(pkg, null, 2));

  console.log(`created: ${app}`);
}
