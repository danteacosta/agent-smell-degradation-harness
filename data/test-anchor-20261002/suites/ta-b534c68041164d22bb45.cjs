module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves both existing documents after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing",
                title: "Original invoice",
                checksum: "matching-content",
              },
              {
                id: "unrelated",
                title: "Unrelated receipt",
                checksum: "different-content",
              },
            ],
            upload: {
              id: "duplicate-upload",
              title: "Renamed duplicate invoice",
              checksum: "matching-content",
            },
          };
        });

        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const assertDocumentsPreserved = async () => {
          const rows = page.locator("section.document");
          assert.equal(await rows.count(), 2);
          assert.equal(
            await page
              .locator('[data-document-id="existing"] h2')
              .textContent(),
            "Original invoice"
          );
          assert.equal(
            await page
              .locator('[data-document-id="unrelated"] h2')
              .textContent(),
            "Unrelated receipt"
          );
          assert.equal(
            await page
              .getByRole("heading", {
                name: "Renamed duplicate invoice",
                exact: true,
              })
              .count(),
            0
          );
        };

        await assertDocumentsPreserved();
        await page
          .getByRole("button", { name: "Upload document", exact: true })
          .click();
        await assertDocumentsPreserved();

        await page.reload();
        await assertDocumentsPreserved();
      },
    },
  ],
};
