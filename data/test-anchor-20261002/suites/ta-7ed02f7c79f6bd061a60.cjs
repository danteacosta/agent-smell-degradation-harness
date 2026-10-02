module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "matching-file-content",
              },
              {
                id: "unrelated-document",
                title: "Unrelated receipt",
                checksum: "different-file-content",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "matching-file-content",
            },
          };
        });

        await page.goto(url);

        const titles = page.getByRole("heading", { level: 2 });
        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          ["Original invoice", "Unrelated receipt"].sort(),
          "Both existing documents should be visible before uploading"
        );

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        const expectedTitles = [
          "Original invoice",
          "Unrelated receipt",
          "Uploaded invoice copy",
        ].sort();

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          expectedTitles,
          "Matching content should create a separate document while preserving both existing documents"
        );

        await page.reload();

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          expectedTitles,
          "All three documents should remain after reloading"
        );
      },
    },
  ],
};
