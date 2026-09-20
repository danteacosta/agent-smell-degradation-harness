// Extend the pinned upstream support without changing its assertions or hooks.
import './e2e.js';

afterEach(function () {
  if (this.currentTest.fullTitle() === 'TodoMVC - vue Editing should cancel edits on escape') {
    cy.screenshot('escape-after-interaction', { capture: 'viewport' });
  }
});
