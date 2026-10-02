module.exports = {
  tests: [
    {
      name: "Default upload accepts duplicate content and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.removeItem("paperless-duplicate-pilot");
          window.initialState = {
            documents: [
              {
                id: "existing",
                title: "Original invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated",
                title: "Unrelated report",
                checksum: "different-file-content",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "identical-file-content",
            },
          };
        });

        await page.goto(url);

        const rows = page.locator(".document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        assert.equal(await rows.count(), 3);
        assert.equal(
          await page.locator('[data-document-id="existing"]').getByRole("heading").textContent(),
          "Original invoice"
        );
        assert.equal(
          await page.locator('[data-document-id="unrelated"]').getByRole("heading").textContent(),
          "Unrelated report"
        );

        const uploadedRow = rows.filter({
          has: page.getByRole("heading", {
            name: "Uploaded invoice copy",
            exact: true,
          }),
        });
        assert.equal(await uploadedRow.count(), 1);

        const newId = await uploadedRow.getAttribute("data-document-id");
        assert.ok(newId, "The uploaded copy must have its own identity");
        assert.notEqual(newId, "existing");
        assert.notEqual(newId, "unrelated");
      },
    },
  ],
};
