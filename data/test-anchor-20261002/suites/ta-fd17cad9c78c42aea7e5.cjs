module.exports = {
  tests: [
    {
      name: "Uploading duplicate content creates a new document and preserves both existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "matching-content" },
              { id: "unrelated", title: "Unrelated receipt", checksum: "other-content" },
            ],
            upload: { name: "Invoice copy", checksum: "matching-content" },
          };
        });

        await page.goto(url, { timeout: 5000 });
        const titles = page.getByRole("heading", { level: 2 });
        assert.deepEqual(await titles.allTextContents(), [
          "Original invoice",
          "Unrelated receipt",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true })
          .click({ timeout: 3000 });
        await page.getByRole("heading", { name: "Invoice copy", exact: true })
          .waitFor({ timeout: 3000 });

        const expected = ["Invoice copy", "Original invoice", "Unrelated receipt"];
        assert.deepEqual((await titles.allTextContents()).sort(), expected);

        await page.reload({ timeout: 5000 });
        assert.deepEqual((await titles.allTextContents()).sort(), expected);
      },
    },
    {
      name: "Duplicate content with the same title remains a separate document after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Invoice", checksum: "matching-content" },
              { id: "unrelated", title: "Receipt", checksum: "other-content" },
            ],
            upload: { title: "Invoice", checksum: "matching-content" },
          };
        });

        await page.goto(url, { timeout: 5000 });
        const titles = page.getByRole("heading", { level: 2 });
        assert.deepEqual((await titles.allTextContents()).sort(), [
          "Invoice",
          "Receipt",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true })
          .click({ timeout: 3000 });
        await page.getByRole("heading", { name: "Invoice", exact: true })
          .nth(1).waitFor({ timeout: 3000 });

        assert.deepEqual((await titles.allTextContents()).sort(), [
          "Invoice",
          "Invoice",
          "Receipt",
        ]);

        await page.reload({ timeout: 5000 });
        assert.deepEqual((await titles.allTextContents()).sort(), [
          "Invoice",
          "Invoice",
          "Receipt",
        ]);
      },
    },
  ],
};
