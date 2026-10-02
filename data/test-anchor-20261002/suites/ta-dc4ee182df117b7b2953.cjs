module.exports = {
  tests: [
    {
      name: "Default upload keeps matching-content documents separately and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "matching-file-content",
              },
              {
                id: "unrelated-document",
                title: "Unrelated report",
                checksum: "different-file-content",
              },
            ],
            upload: {
              name: "Uploaded invoice copy",
              checksum: "matching-file-content",
            },
          };
        });

        await page.goto(url);
        const titles = page.locator("#documents .document h2");

        assert.deepEqual(await titles.allTextContents(), [
          "Original invoice",
          "Unrelated report",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true })
          .click({ timeout: 3000 });

        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        assert.equal(await page.locator("#documents .document").count(), 3);
        assert.deepEqual((await titles.allTextContents()).sort(), [
          "Original invoice",
          "Unrelated report",
          "Uploaded invoice copy",
        ].sort());

        for (const title of [
          "Original invoice",
          "Unrelated report",
          "Uploaded invoice copy",
        ]) {
          assert.equal(
            await page.getByRole("heading", { name: title, exact: true })
              .isVisible(),
            true,
            `${title} should remain visible after uploading matching content`
          );
        }
      },
    },
  ],
};
