'use strict';

function createCappedDeduplicator(limit) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new TypeError('positive integer limit required');
  }
  const seen = new Set();
  const values = [];
  return {
    add(key, value) {
      if (values.length >= limit || seen.has(key)) return false;
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

module.exports = {createCappedDeduplicator};
