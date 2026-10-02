module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves existing and unrelated documents after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
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
              id: "uploaded",
              title: "Uploaded invoice copy",
              checksum: "identical-file-content",
            },
          };
        });

        await page.goto(url);

        const titles = page.getByRole("heading", { level: 2 });
        const expected = ["Original invoice", "Unrelated report"];

        assert.deepEqual((await titles.allTextContents()).sort(), expected);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          expected,
          "Uploading duplicate content must preserve both documents without adding a copy"
        );

        await page.reload();

        assert.deepEqual(
          (await titles.allTextContents()).sort(),
          expected,
          "Both original documents must remain preserved after reload"
        );
      },
    },
  ],
};
