const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const header = fs.readFileSync(path.join(__dirname, '../src/readonly_diagnostics.h'), 'utf8');
const probe = header.split('R"JS(')[1].split(')JS"')[0];
const element = (value, visible = true, label = '') => Object.freeze({
  innerText: value, textContent: value,
  getClientRects: () => visible ? [{}] : [],
  getAttribute: key => key === 'aria-label' ? label : null
});
function run({host = 'client.pragmaticplaylive.net', page = '/desktop/baccarat/',
              balances = [], total = [], mobileBalance = [], mobileTotal = [], menus = [], password = [], tiles = [], body = ''} = {}) {
  const document = Object.freeze({
    body: element(body),
    querySelectorAll(selector) {
      if (selector.includes('wallet-balance-value')) return [...balances, ...(selector.includes('[data-testid="wallet-mobile-balance"] [data-testid="wallet-mobile-value"]') ? mobileBalance : [])];
      if (selector.includes('wallet-total-bet-value')) return [...total, ...(selector.includes('[data-testid="wallet-mobile-total-bet"] [data-testid="wallet-mobile-value"]') ? mobileTotal : [])];
      if (selector === '[role="combobox"]') return menus;
      if (selector === 'input[type="password"]') return password;
      if (selector === '[id^="TileHeight-"]') return tiles;
      throw Error(`unexpected selector: ${selector}`);
    }
  });
  return JSON.parse(vm.runInNewContext(probe, {
    document, location: Object.freeze({hostname: host, pathname: page}),
    getComputedStyle: () => Object.freeze({visibility: 'visible', display: 'block'})
  }, {timeout: 1000}));
}
const desktop = run({balances: [element('12,34 €')], total: [element('5,00 €')], body: 'ID: 1234'});
assert.equal(desktop.providerBalance, '12,34 €');
assert.equal(desktop.totalBet, '5,00 €');
const mobile = run({balances: [element('999 €', false)], total: [element('888 €', false)], mobileBalance: [element('12,34 €')], mobileTotal: [element('1,40 €')]});
assert.equal(mobile.providerBalance, '12,34 €');
assert.equal(mobile.totalBet, '1,40 €');
assert.equal(run({mobileTotal: [element('0,00 €')]}).providerBalance, null);
assert.equal(run({mobileBalance: [element('0,00 €')]}).totalBet, null);
assert.equal(desktop.casinoBalance, undefined);
assert.deepEqual(desktop.rounds, ['ID: 1234']);
assert.equal(run({balances: [element('999 €', false), element('0,00 €')]}).providerBalance, '0,00 €');
assert.equal(run({total: [element('123 €')]}).providerBalance, null);
assert.deepEqual(run({host: 'evil.rooster.bet.example'}), {kind: 'bridge'});
assert.equal(run({host: 'www.rooster.bet'}).casinoBalance, null);
assert.equal(run({host: 'www.rooster.bet'}).login, 'unknown');
assert.equal(run({host: 'www.rooster.bet', menus: [element('7,89 €', true, 'Currency'), element('', true, 'User Menu')]}).casinoBalance, '7,89 €');
assert.equal(run({host: 'rooster.bet', menus: [element('', true, 'User Menu')], password: [element('')]}).login, 'login-visible');
assert.equal(run({body: 'Sitzung abgelaufen'}).expired, true);
assert.equal(run({page: '/desktop/multibaccarat/', tiles: [{}, {}]}).tableCount, 2);
assert.equal(run({page: '/desktop/multibaccarat/'}).view, 'MULTIPLAY');
console.log('PASS: production probe; desktop/mobile balance, total-bet separation, unknown auth, exact origins, expiry, table count');
