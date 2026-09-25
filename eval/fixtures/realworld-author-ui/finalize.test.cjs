'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {finalize} = require('./finalize.cjs');

const COMMON = {
  schema_version: 'realworld-author-ui-browser/v1',
  app_sha256: 'a'.repeat(64),
  runner_version: '1',
  browser_sandbox: false,
  isolation: 'fresh context per fixture',
};

test('close rejection still writes one exact browser failure report', async () => {
  const writes = [];
  const complete = {
    ...COMMON,
    status: 'complete',
    browser_version: 'Chromium',
    observations: [],
    target_failed: [],
  };

  const outcome = await finalize({
    browser: {close: async () => { throw new Error('x'.repeat(2000)); }},
    report: complete,
    exitCode: 0,
    browserStarted: true,
    outputPath: '/output/report.json',
    writeFile: (path, value) => writes.push([path, value]),
  });

  assert.equal(writes.length, 1);
  assert.equal(writes[0][0], '/output/report.json');
  const written = JSON.parse(writes[0][1]);
  assert.deepEqual(Object.keys(written).sort(), [
    'app_sha256', 'browser_sandbox', 'browser_started', 'error', 'isolation',
    'runner_version', 'schema_version', 'status',
  ]);
  assert.equal(written.status, 'browser_failure');
  assert.equal(written.browser_started, true);
  assert.equal(written.error.length, 1500);
  assert.equal(outcome.exitCode, 21);
  assert.deepEqual(outcome.report, written);
});

test('normal close writes the supplied report and preserves its exit code', async () => {
  const writes = [];
  let closes = 0;
  const supplied = {...COMMON, status: 'complete', observations: []};

  const outcome = await finalize({
    browser: {close: async () => { closes += 1; }},
    report: supplied,
    exitCode: 10,
    browserStarted: true,
    outputPath: '/output/report.json',
    writeFile: (path, value) => writes.push([path, value]),
  });

  assert.equal(closes, 1);
  assert.equal(writes.length, 1);
  assert.equal(writes[0][0], '/output/report.json');
  assert.deepEqual(JSON.parse(writes[0][1]), supplied);
  assert.deepEqual(outcome, {report: supplied, exitCode: 10});
});
