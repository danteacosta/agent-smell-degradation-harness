'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  MatchOverflowError,
  createCappedDeduplicator,
  requireBoundedCount,
} = require('./author-matches.cjs');

test('author matches deduplicate across scopes before the global cap', () => {
  const matches = createCappedDeduplicator(20);
  for (let index = 0; index < 20; index += 1) {
    matches.add(`node-${index}`, {id: index});
    matches.add(`node-${index}`, {id: `duplicate-${index}`});
  }

  assert.equal(matches.full, true);
  assert.equal(matches.values.length, 20);
  assert.deepEqual(matches.values.map((item) => item.id),
    Array.from({length: 20}, (_, index) => index));
  assert.throws(() => matches.add('node-20', {id: 20}), MatchOverflowError);
});

test('general locator counts fail closed instead of clamping', () => {
  assert.equal(requireBoundedCount(20, 20, 'button'), 20);
  assert.throws(() => requireBoundedCount(21, 20, 'button'),
    MatchOverflowError);
});
