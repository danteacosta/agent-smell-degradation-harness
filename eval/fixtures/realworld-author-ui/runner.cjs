'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');

const URL = 'http://fixture.invalid/article/bounded-ui-case';
const TITLE = 'Bounded UI case';
const BODY = 'Observable article body';
const VIEWPORT = {width: 1000, height: 720};
const GRID = {dimension: 5, inset_ratio: 0.08};
const PAIRS = [
  ['article-alice', 'author', 'alice', 'alice'],
  ['article-alice', 'non-author', 'alice', 'bob'],
  ['article-bob', 'author', 'bob', 'bob'],
  ['article-bob', 'non-author', 'bob', 'alice'],
];
const SCREENSHOTS = PAIRS.map(([fixture, context]) => `${fixture}-${context}.png`);
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
const html = fs.readFileSync('/input/app.html');
const report = {
  schema_version: 'realworld-author-ui-browser/v1',
  status: 'browser_failure',
  app_sha256: crypto.createHash('sha256').update(html).digest('hex'),
  runner_version: '1',
  browser_sandbox: false,
  isolation: 'non-root offline resource-bounded Docker; fresh browser context per fixture/viewer pair; browser sandbox disabled',
};

let browser;
let browserStarted = false;
let exitCode = 21;

class InterfaceError extends Error {}

function stateFor(articleUsername, viewerUsername) {
  return {
    viewer: {username: viewerUsername},
    article: {
      slug: 'bounded-ui-case',
      title: TITLE,
      body: BODY,
      author: {username: articleUsername},
    },
  };
}

function validateState(state) {
  if (!state || !state.viewer || typeof state.viewer.username !== 'string'
      || !state.article || state.article.slug !== 'bounded-ui-case'
      || state.article.title !== TITLE || state.article.body !== BODY
      || !state.article.author
      || typeof state.article.author.username !== 'string') {
    throw new InterfaceError('initialState requires viewer and article author usernames plus the fixed article fields');
  }
}

async function installState(context, state) {
  await context.addInitScript((payload) => {
    const freeze = (value) => {
      if (value && typeof value === 'object' && !Object.isFrozen(value)) {
        for (const child of Object.values(value)) freeze(child);
        Object.freeze(value);
      }
      return value;
    };
    Object.defineProperty(window, 'initialState', {
      value: freeze(payload),
      writable: false,
      configurable: false,
      enumerable: true,
    });
  }, state);
}

function validBox(box) {
  return box !== null
    && [box.x, box.y, box.width, box.height].every(Number.isFinite)
    && box.width >= 1 && box.height >= 1;
}

async function perceptible(locator) {
  try {
    if (!await locator.isVisible()) return false;
    let box = await locator.boundingBox();
    if (!validBox(box)) return false;
    const opacity = await locator.evaluate((node) => {
      let product = 1;
      for (let current = node; current; current = current.parentElement) {
        product *= Number.parseFloat(getComputedStyle(current).opacity);
      }
      return product;
    });
    if (!Number.isFinite(opacity) || opacity <= 0.01) return false;
    await locator.scrollIntoViewIfNeeded();
    box = await locator.boundingBox();
    if (!validBox(box)) return false;
    const left = Math.max(0, box.x);
    const top = Math.max(0, box.y);
    const right = Math.min(VIEWPORT.width, box.x + box.width);
    const bottom = Math.min(VIEWPORT.height, box.y + box.height);
    if (right - left < 1 || bottom - top < 1) return false;
    const points = [];
    for (let row = 0; row < GRID.dimension; row += 1) {
      for (let column = 0; column < GRID.dimension; column += 1) {
        const xRatio = GRID.inset_ratio
          + (1 - 2 * GRID.inset_ratio) * column / (GRID.dimension - 1);
        const yRatio = GRID.inset_ratio
          + (1 - 2 * GRID.inset_ratio) * row / (GRID.dimension - 1);
        points.push({
          x: left + (right - left) * xRatio,
          y: top + (bottom - top) * yRatio,
        });
      }
    }
    return await locator.evaluate((node, samples) => {
      const chain = [];
      for (let current = node; current; current = current.parentElement) {
        chain.push({
          node: current,
          value: current.style.getPropertyValue('pointer-events'),
          priority: current.style.getPropertyPriority('pointer-events'),
        });
      }
      try {
        for (const item of chain) {
          item.node.style.setProperty('pointer-events', 'auto', 'important');
        }
        return samples.some(({x, y}) => {
          const hit = document.elementFromPoint(x, y);
          return hit === node || (hit !== null && node.contains(hit));
        });
      } finally {
        for (const item of chain) {
          if (item.value === '') item.node.style.removeProperty('pointer-events');
          else item.node.style.setProperty('pointer-events', item.value, item.priority);
        }
      }
    }, points);
  } catch (_) {
    return false;
  }
}

async function observeLocator(locator) {
  const rawCount = await locator.count();
  const matched = Math.min(rawCount, 20);
  let visible = 0;
  for (let index = 0; index < matched; index += 1) {
    if (await perceptible(locator.nth(index))) visible += 1;
  }
  return {matched, perceptible: visible};
}

async function authorLocators(page, expected) {
  const scopes = page.locator('[rel~="author"]');
  const unique = [];
  const keys = new Set();
  const scopeCount = Math.min(await scopes.count(), 20);
  for (let scopeIndex = 0; scopeIndex < scopeCount; scopeIndex += 1) {
    const matches = scopes.nth(scopeIndex).getByText(expected, {exact: true});
    const count = Math.min(await matches.count(), 20);
    for (let index = 0; index < count; index += 1) {
      const candidate = matches.nth(index);
      const key = await candidate.evaluate((node) => {
        const path = [];
        for (let current = node; current && current.parentElement;
             current = current.parentElement) {
          path.push(Array.prototype.indexOf.call(
            current.parentElement.children, current));
        }
        return path.reverse().join('/');
      });
      if (!keys.has(key)) {
        keys.add(key);
        unique.push(candidate);
      }
    }
  }
  return unique;
}

async function observeAuthor(page, expected) {
  const matches = await authorLocators(page, expected);
  let visible = 0;
  for (const locator of matches) {
    if (await perceptible(locator)) visible += 1;
  }
  return {matched: matches.length, perceptible: visible};
}

async function observeContext(fixtureId, contextId, articleUsername, viewerUsername) {
  const context = await browser.newContext({
    viewport: VIEWPORT,
    serviceWorkers: 'block',
    acceptDownloads: false,
  });
  try {
    const state = stateFor(articleUsername, viewerUsername);
    validateState(state);
    await installState(context, state);
    await context.route('**/*', (route) => {
      const request = route.request();
      if (request.url() === URL && request.isNavigationRequest()) {
        return route.fulfill({
          status: 200,
          body: html,
          contentType: 'text/html',
          headers: {'Content-Security-Policy': CSP},
        });
      }
      return route.abort();
    });
    const page = await context.newPage();
    page.setDefaultTimeout(2500);
    const runtimeErrors = [];
    const record = (kind, message) => {
      if (runtimeErrors.length < 20) {
        runtimeErrors.push({kind, message: String(message).slice(0, 500)});
      }
    };
    page.on('console', (message) => {
      if (message.type() === 'error') record('console', message.text());
    });
    page.on('pageerror', (error) => record('page', error));
    page.on('dialog', (dialog) => dialog.dismiss());
    await page.goto(URL, {waitUntil: 'load', timeout: 10000});
    await page.waitForTimeout(300);

    const title = await observeLocator(page.getByText(TITLE, {exact: true}));
    const body = await observeLocator(page.getByText(BODY, {exact: true}));
    const articleAuthor = await observeAuthor(page, articleUsername);
    const deleteButtons = await observeLocator(
      page.getByRole('button', {name: /^Delete\s+Article$/i}));
    const screenshot = `${fixtureId}-${contextId}.png`;
    await page.screenshot({path: `/output/${screenshot}`});
    return {
      fixture_id: fixtureId,
      context_id: contextId,
      final_url: page.url(),
      title,
      body,
      article_author: articleAuthor,
      delete_buttons: deleteButtons,
      runtime_errors: runtimeErrors,
      screenshot,
    };
  } finally {
    await context.close();
  }
}

function deriveClaims(observations) {
  const failed = new Set();
  const reasons = [];
  for (const observation of observations) {
    const assertion = observation.context_id === 'author'
      ? 'author_sees_delete_article'
      : 'non_author_does_not_see_delete_article';
    const missing = [];
    if (observation.final_url !== URL) missing.push('route_mismatch');
    if (observation.title.perceptible < 1) missing.push('title_missing');
    if (observation.body.perceptible < 1) missing.push('body_missing');
    if (observation.article_author.perceptible < 1) {
      missing.push('article_author_missing');
    }
    if (missing.length > 0) {
      for (const reason of missing) {
        reasons.push({
          assertion_id: assertion,
          fixture_id: observation.fixture_id,
          context_id: observation.context_id,
          reason,
        });
      }
    } else if (observation.context_id === 'author'
               && observation.delete_buttons.perceptible === 0) {
      failed.add(assertion);
    } else if (observation.context_id === 'non-author'
               && observation.delete_buttons.perceptible >= 1) {
      failed.add(assertion);
    }
  }
  reasons.sort((left, right) => {
    const a = [left.assertion_id, left.fixture_id, left.context_id, left.reason].join('\0');
    const b = [right.assertion_id, right.fixture_id, right.context_id, right.reason].join('\0');
    return a < b ? -1 : a > b ? 1 : 0;
  });
  return {
    failed: [...failed].sort(),
    notEvaluable: [...new Set(reasons.map((item) => item.assertion_id))].sort(),
    reasons,
  };
}

async function run() {
  const args = process.argv.slice(2);
  if (args.length > 1 || (args.length === 1 && ![
    '--qualify-invalid-interface', '--qualify-browser-failure',
  ].includes(args[0]))) {
    throw new InterfaceError('unsupported runner arguments');
  }
  if (args[0] === '--qualify-invalid-interface') {
    const invalid = stateFor('alice', 'alice');
    delete invalid.article.author.username;
    validateState(invalid);
    throw new InterfaceError('invalid interface control unexpectedly passed');
  }

  browser = await chromium.launch({headless: true, chromiumSandbox: false});
  browserStarted = true;
  if (args[0] === '--qualify-browser-failure') {
    throw new Error('deliberate browser failure qualification control');
  }

  const observations = [];
  for (const pair of PAIRS) observations.push(await observeContext(...pair));
  const claims = deriveClaims(observations);
  Object.assign(report, {
    status: 'complete',
    browser_version: browser.version(),
    viewport: VIEWPORT,
    sample_grid: GRID,
    observations,
    target_failed: claims.failed,
    target_not_evaluable: claims.notEvaluable,
    not_evaluable_reasons: claims.reasons,
    screenshots: SCREENSHOTS,
  });
  exitCode = claims.notEvaluable.length > 0 ? 11 : claims.failed.length > 0 ? 10 : 0;
}

(async () => {
  try {
    await run();
  } catch (error) {
    report.status = error instanceof InterfaceError
      ? 'interface_failure' : 'browser_failure';
    report.error = String(error).slice(0, 1500);
    report.browser_started = browserStarted;
    exitCode = error instanceof InterfaceError ? 20 : 21;
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync('/output/report.json', JSON.stringify(report, null, 2));
    process.exitCode = exitCode;
  }
})();
