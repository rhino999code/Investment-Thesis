// Usage: NODE_PATH=/opt/node22/lib/node_modules node render.js in.html out.pdf [nofooter]
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [,, inHtml, outPdf, mode] = process.argv;
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(inHtml), { waitUntil: 'load' });
  await page.emulateMedia({ media: 'print' });
  const footer = `
    <div style="width:100%; font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif; font-size:7.5pt; color:#7a8494; padding:0 15mm; display:flex; justify-content:space-between; align-items:center;">
      <span>과부하의 시대 · 2026–2037 투자 Thesis</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
    </div>`;
  const opts = { path: outPdf, format: 'A4', printBackground: true, preferCSSPageSize: true };
  if (mode !== 'nofooter') {
    Object.assign(opts, { displayHeaderFooter: true, headerTemplate: '<div></div>', footerTemplate: footer });
  }
  await page.pdf(opts);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
