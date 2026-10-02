module.exports = {
  tests: [
    {
      name: "Default upload accepts duplicate content and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "same-content" },
              { id: "unrelated", title: "Unrelated receipt", checksum: "other-content" },
            ],
            upload: { title: "Uploaded invoice copy", checksum: "same-content" },
          };
        });

        await page.goto(url);
        const titles = page.locator("#documents .document h2");
        assert.deepEqual(await titles.allTextContents(), [
          "Original invoice",
          "Unrelated receipt",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", { name: "Uploaded invoice copy", exact: true })
          .waitFor({ state: "visible", timeout: 3000 });

        assert.equal(await page.locator("#documents .document").count(), 3);
        assert.deepEqual((await titles.allTextContents()).sort(), [
          "Original invoice",
          "Unrelated receipt",
          "Uploaded invoice copy",
        ].sort());
      },
    },
    {
      name: "Duplicate content with the same title creates a separate document",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          // Seed once so a reload verifies the application's saved documents.
          if (!sessionStorage.getItem("duplicate-test-seeded")) {
            localStorage.clear();
            sessionStorage.setItem("duplicate-test-seeded", "true");
          }
          window.initialState = {
            documents: [
              { id: "original", title: "Invoice", checksum: "same-content" },
              { id: "unrelated", title: "Receipt", checksum: "other-content" },
            ],
            upload: { title: "Invoice", checksum: "same-content" },
          };
        });

        await page.goto(url);
        assert.equal(await page.locator("#documents .document").count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", { name: "Invoice", exact: true })
          .nth(1).waitFor({ state: "visible", timeout: 3000 });

        assert.deepEqual(
          (await page.locator("#documents .document h2").allTextContents()).sort(),
          ["Invoice", "Invoice", "Receipt"]
        );
        assert.equal(await page.locator("#documents .document").count(), 3);

        await page.reload();
        await page.getByRole("heading", { name: "Invoice", exact: true })
          .nth(1).waitFor({ state: "visible", timeout: 3000 });

        assert.equal(await page.locator("#documents .document").count(), 3);
        assert.deepEqual(
          (await page.locator("#documents .document h2").allTextContents()).sort(),
          ["Invoice", "Invoice", "Receipt"]
        );
      },
    },
  ],
};
