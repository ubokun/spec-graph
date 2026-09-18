import { copyFileSync, readFileSync, writeFileSync } from 'node:fs';
const assets = 'spec_graph/assets/';
const packages = [
  ['cytoscape', 'dist/cytoscape.min.js', 'cytoscape.min.js', 'LICENSE'],
  ['cytoscape-dagre', 'dist/cytoscape-dagre.min.js', 'cytoscape-dagre.min.js', 'LICENSE']
];
let notices = '# Third-party licenses\n\nGenerated with npm run vendor. Runtime assets are served locally.\n';
for (const [name, source, target, license] of packages) {
  const base = `node_modules/${name}/`;
  copyFileSync(base + source, assets + target);
  const meta = JSON.parse(readFileSync(base + 'package.json', 'utf8'));
  notices += `\n## ${name} ${meta.version}\n\n${readFileSync(base + license, 'utf8')}\n`;
}
for (const name of ['@dagrejs/dagre', '@dagrejs/graphlib']) {
  const base = `node_modules/${name}/`;
  const meta = JSON.parse(readFileSync(base + 'package.json', 'utf8'));
  notices += `\n## Bundled ${name} ${meta.version}\n\n${readFileSync(base + 'LICENSE', 'utf8')}\n`;
}
notices += '\n' + readFileSync('node_modules/@dagrejs/dagre/dist/dagre.esm.js.LEGAL.txt', 'utf8');
writeFileSync(assets + 'THIRD_PARTY_LICENSES.txt', notices);
