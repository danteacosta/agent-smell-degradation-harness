#!/bin/bash
# Runs only inside the pinned, credential-free, offline pilot container.
set -uo pipefail
export HOME=/tmp/home
cp -a /opt/cypress-cache /tmp/cypress-cache
export CYPRESS_CACHE_FOLDER=/tmp/cypress-cache
mkdir -p "$HOME" /tmp/todomvc
cp -a /opt/todomvc/. /tmp/todomvc/
cd /tmp/todomvc || exit 70
if [ -f /input/response.json ]; then
  node <<'NODE' > /output/body-validation.log 2>&1
const fs = require('fs');
const acorn = require('/opt/body-validator/node_modules/acorn');
const response = JSON.parse(fs.readFileSync('/input/response.json', 'utf8'));
const program = acorn.parse('function handleEscape() {\n' + response.handler_body + '\n}', {ecmaVersion: 'latest'});
if (program.body.length !== 1 || program.body[0].type !== 'FunctionDeclaration' || program.body[0].id.name !== 'handleEscape') {
  throw new Error('Response must remain inside the handler body');
}
NODE
  body_status=$?
  if [ "$body_status" -ne 0 ]; then exit "$body_status"; fi
fi
if [ -f /input/TodoItem.vue ]; then
  cp /input/TodoItem.vue examples/vue/src/components/TodoItem.vue
fi
cp examples/vue/src/components/TodoItem.vue /output/executed-TodoItem.vue
npm --prefix examples/vue run build > /output/build.log 2>&1
build_status=$?
if [ "$build_status" -ne 0 ]; then
  echo "$build_status" > /output/build-exit-code.txt
  exit "$build_status"
fi
npx --no-install start-server-and-test server http://localhost:8000 \
  'cypress run --browser electron --config video=true,supportFile=cypress/support/qualification-visual.js --env framework=vue --spec cypress/e2e/spec.cy.js --reporter junit --reporter-options mochaFile=todomvc-qualification-junit.xml' \
  > /output/e2e.log 2>&1
test_status=$?
for item in todomvc-qualification-junit.xml cypress/screenshots cypress/videos; do
  if [ -e "$item" ]; then cp -a "$item" /output/; fi
done
echo "$test_status" > /output/e2e-exit-code.txt
exit "$test_status"
