module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves both existing documents without adding a copy",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated-document",
                title: "Unrelated receipt",
                checksum: "different-file-content",
              },
            ],
            upload: {
              id: "new-upload",
              title: "Renamed invoice copy",
              checksum: "identical-file-content",
            },
          };
        });

        await page.goto(url);
        const titles = page.locator("#documents .document h2");
        const expected = ["Original invoice", "Unrelated receipt"];

        assert.deepEqual(await titles.allTextContents(), expected);

        await page.getByRole("button", { name: "Upload document" }).click();

        assert.deepEqual(
          await titles.allTextContents(),
          expected,
          "Uploading matching content must preserve the original and unrelated document without adding a duplicate"
        );

        await page.reload();

        assert.deepEqual(
          await titles.allTextContents(),
          expected,
          "Both preserved documents must remain unchanged after reloading"
        );
      },
    },
  ],
};
