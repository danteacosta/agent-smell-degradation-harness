'use strict';

class MatchOverflowError extends Error {}

function requireBoundedCount(rawCount, limit, label) {
  if (!Number.isInteger(rawCount) || rawCount < 0) {
    throw new TypeError('nonnegative integer count required');
  }
  if (rawCount > limit) {
    throw new MatchOverflowError(`${label} matched more than ${limit} elements`);
  }
  return rawCount;
}

function createCappedDeduplicator(limit) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new TypeError('positive integer limit required');
  }
  const seen = new Set();
  const values = [];
  return {
    add(key, value) {
      if (seen.has(key)) return false;
      if (values.length >= limit) {
        throw new MatchOverflowError(`unique match count exceeded ${limit}`);
      }
      seen.add(key);
      values.push(value);
      return true;
    },
    get full() {
      return values.length >= limit;
    },
    values,
  };
}

module.exports = {
  MatchOverflowError,
  createCappedDeduplicator,
  requireBoundedCount,
};
