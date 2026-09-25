'use strict';

const fs = require('node:fs');

function browserFailure(report, browserStarted, error) {
  return {
    schema_version: report.schema_version,
    status: 'browser_failure',
    app_sha256: report.app_sha256,
    runner_version: report.runner_version,
    browser_sandbox: report.browser_sandbox,
    isolation: report.isolation,
    error: `browser close failed: ${String(error)}`.slice(0, 1500),
    browser_started: browserStarted,
  };
}

async function finalize({browser, report, exitCode, browserStarted, outputPath,
                         writeFile = fs.writeFileSync}) {
  let finalReport = report;
  let finalExitCode = exitCode;
  try {
    try {
      if (browser) await browser.close();
    } catch (error) {
      finalReport = browserFailure(report, browserStarted, error);
      finalExitCode = 21;
    }
  } finally {
    writeFile(outputPath, JSON.stringify(finalReport, null, 2));
  }
  return {report: finalReport, exitCode: finalExitCode};
}

module.exports = {finalize};
