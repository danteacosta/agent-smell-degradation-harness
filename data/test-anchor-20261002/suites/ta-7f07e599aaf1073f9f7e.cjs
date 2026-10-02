module.exports = {
  tests: [
    {
      name: "Default upload creates a separate document for duplicate content",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
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
        const titles = page.getByRole("heading", { level: 2 });

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          ["Original invoice", "Unrelated report"].sort()
        );

        await page.getByRole("button", {
          name: "Upload document",
          exact: true,
        }).click();

        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          [
            "Original invoice",
            "Unrelated report",
            "Uploaded invoice copy",
          ].sort(),
          "The duplicate upload should appear alongside both preserved documents"
        );
      },
    },
  ],
};
