module.exports = {
  tests: [
    {
      name: "Default upload accepts duplicate content as a separate document",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.removeItem("paperless-duplicate-pilot");
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "same-content-checksum",
                content: "Invoice content",
              },
              {
                id: "unrelated-document",
                title: "Unrelated report",
                checksum: "different-content-checksum",
                content: "Report content",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              name: "Uploaded invoice copy",
              checksum: "same-content-checksum",
              content: "Invoice content",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document" }).click();

        await page.waitForFunction(
          () => document.querySelectorAll("#documents .document").length === 3,
          undefined,
          { timeout: 5000 }
        );

        assert.equal(await rows.count(), 3);
        assert.equal(
          await page
            .locator('[data-document-id="existing-document"] h2')
            .textContent(),
          "Original invoice"
        );
        assert.equal(
          await page
            .locator('[data-document-id="unrelated-document"] h2')
            .textContent(),
          "Unrelated report"
        );

        const uploaded = rows.filter({
          has: page.getByRole("heading", {
            name: "Uploaded invoice copy",
            exact: true,
          }),
        });
        assert.equal(await uploaded.count(), 1);

        const newId = await uploaded.getAttribute("data-document-id");
        assert.ok(newId, "The uploaded document has its own identity");
        assert.notEqual(newId, "existing-document");
        assert.notEqual(newId, "unrelated-document");

        const identities = await rows.evaluateAll(elements =>
          elements.map(element => element.dataset.documentId)
        );
        assert.equal(new Set(identities).size, 3);
      },
    },
  ],
};
