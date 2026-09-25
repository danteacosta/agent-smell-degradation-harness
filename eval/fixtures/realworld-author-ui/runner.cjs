'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const {
  MatchOverflowError,
  createCappedDeduplicator,
  requireBoundedCount,
} = require('./author-matches.cjs');
const {finalize} = require('./finalize.cjs');

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
    const trusted = {
      getComputedStyle: window.getComputedStyle.bind(window),
      elementFromPoint: document.elementFromPoint.bind(document),
      parseFloat: Number.parseFloat,
      indexOf: Function.prototype.call.bind(Array.prototype.indexOf),
      includes: Function.prototype.call.bind(Array.prototype.includes),
      contains: Function.prototype.call.bind(Node.prototype.contains),
      parentElement: Function.prototype.call.bind(
        Object.getOwnPropertyDescriptor(Node.prototype, 'parentElement').get),
      children: Function.prototype.call.bind(
        Object.getOwnPropertyDescriptor(Element.prototype, 'children').get),
      style: Function.prototype.call.bind(
        Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'style').get),
      getPropertyValue: Function.prototype.call.bind(
        CSSStyleDeclaration.prototype.getPropertyValue),
      getPropertyPriority: Function.prototype.call.bind(
        CSSStyleDeclaration.prototype.getPropertyPriority),
      setProperty: Function.prototype.call.bind(
        CSSStyleDeclaration.prototype.setProperty),
      removeProperty: Function.prototype.call.bind(
        CSSStyleDeclaration.prototype.removeProperty),
    };
    const lockArrayPrimitive = (key) => {
      const descriptor = Object.getOwnPropertyDescriptor(Array.prototype, key);
      Object.defineProperty(Array.prototype, key, {
        ...descriptor,
        writable: false,
        configurable: false,
      });
    };
    lockArrayPrimitive('indexOf');
    lockArrayPrimitive('includes');
    lockArrayPrimitive('push');
    lockArrayPrimitive(Symbol.iterator);
    for (const value of Object.values(trusted)) Object.freeze(value);
    Object.freeze(trusted);
    Object.defineProperty(window, '__realworldTrustedPrimitivesV1', {
      value: trusted,
      writable: false,
      configurable: false,
      enumerable: false,
    });
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
      const trusted = window.__realworldTrustedPrimitivesV1;
      let product = 1;
      for (let current = node; current; current = trusted.parentElement(current)) {
        const style = trusted.getComputedStyle(current);
        product *= trusted.parseFloat(
          trusted.getPropertyValue(style, 'opacity'));
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
      const trusted = window.__realworldTrustedPrimitivesV1;
      const chain = [];
      for (let current = node; current; current = trusted.parentElement(current)) {
        const style = trusted.style(current);
        chain[chain.length] = {
          node: current,
          style,
          value: trusted.getPropertyValue(style, 'pointer-events'),
          priority: trusted.getPropertyPriority(style, 'pointer-events'),
        };
      }
      try {
        for (let index = 0; index < chain.length; index += 1) {
          trusted.setProperty(
            chain[index].style, 'pointer-events', 'auto', 'important');
        }
        for (let index = 0; index < samples.length; index += 1) {
          const hit = trusted.elementFromPoint(
            samples[index].x, samples[index].y);
          if (hit === node || (hit !== null && trusted.contains(node, hit))) {
            return true;
          }
        }
        return false;
      } finally {
        for (let index = 0; index < chain.length; index += 1) {
          const item = chain[index];
          if (item.value === '') {
            trusted.removeProperty(item.style, 'pointer-events');
          } else {
            trusted.setProperty(
              item.style, 'pointer-events', item.value, item.priority);
          }
        }
      }
    }, points);
  } catch (_) {
    return false;
  }
}

async function observeLocator(locator, label) {
  const matched = requireBoundedCount(await locator.count(), 20, label);
  let visible = 0;
  for (let index = 0; index < matched; index += 1) {
    if (await perceptible(locator.nth(index))) visible += 1;
  }
  return {matched, perceptible: visible};
}

async function authorLocators(page, expected) {
  const scopes = page.locator('[rel~="author"]');
  const unique = createCappedDeduplicator(20);
  const scopeCount = await scopes.count();
  for (let scopeIndex = 0; scopeIndex < scopeCount; scopeIndex += 1) {
    const matches = scopes.nth(scopeIndex).getByText(expected, {exact: true});
    const count = await matches.count();
    for (let index = 0; index < count; index += 1) {
      const candidate = matches.nth(index);
      const key = await candidate.evaluate((node) => {
        const trusted = window.__realworldTrustedPrimitivesV1;
        let path = '';
        for (let current = node; current;) {
          const parent = trusted.parentElement(current);
          if (parent === null) break;
          const position = trusted.indexOf(trusted.children(parent), current);
          path = `${position}/${path}`;
          current = parent;
        }
        return path;
      });
      unique.add(key, candidate);
    }
  }
  return unique.values;
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

    const title = await observeLocator(
      page.getByText(TITLE, {exact: true}), 'title');
    const body = await observeLocator(
      page.getByText(BODY, {exact: true}), 'body');
    const articleAuthor = await observeAuthor(page, articleUsername);
    const deleteButtons = await observeLocator(
      page.getByRole('button', {name: /^Delete\s+Article$/i}), 'delete button');
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
    const interfaceFailure = error instanceof InterfaceError
      || error instanceof MatchOverflowError;
    report.status = interfaceFailure
      ? 'interface_failure' : 'browser_failure';
    report.error = String(error).slice(0, 1500);
    report.browser_started = browserStarted;
    exitCode = interfaceFailure ? 20 : 21;
  } finally {
    const outcome = await finalize({
      browser,
      report,
      exitCode,
      browserStarted,
      outputPath: '/output/report.json',
    });
    process.exitCode = outcome.exitCode;
  }
})();
