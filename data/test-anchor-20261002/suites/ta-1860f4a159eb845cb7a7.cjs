module.exports = {
  tests: [
    {
      name: "Matching content creates a new document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "matching-content" },
              { id: "unrelated", title: "Unrelated report", checksum: "other-content" },
            ],
            upload: { name: "Uploaded invoice copy", checksum: "matching-content" },
          };
        });

        await page.goto(url);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), [
          "Original invoice",
          "Unrelated report",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", { name: "Uploaded invoice copy", exact: true }).waitFor({
          timeout: 3000,
        });

        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Original invoice", "Unrelated report", "Uploaded invoice copy"].sort()
        );
      },
    },
    {
      name: "Matching content and filename still create separate documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Invoice.pdf", checksum: "matching-content" },
              { id: "unrelated", title: "Report.pdf", checksum: "other-content" },
            ],
            upload: { name: "Invoice.pdf", checksum: "matching-content" },
          };
        });

        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        assert.equal(await page.getByRole("heading", { level: 2 }).count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", { name: "Invoice.pdf", exact: true }).nth(1).waitFor({
          timeout: 3000,
        });

        assert.equal(await page.getByRole("heading", { level: 2 }).count(), 3);
        assert.equal(await page.getByRole("heading", { name: "Invoice.pdf", exact: true }).count(), 2);
        assert.equal(await page.getByRole("heading", { name: "Report.pdf", exact: true }).count(), 1);

        await page.reload();

        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Invoice.pdf", "Invoice.pdf", "Report.pdf"].sort()
        );
      },
    },
  ],
};
