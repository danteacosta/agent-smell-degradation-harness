module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves the existing and unrelated documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "existing", title: "Existing document", checksum: "matching-content" },
              { id: "unrelated", title: "Unrelated document", checksum: "other-content" },
            ],
            upload: {
              id: "incoming",
              title: "Uploaded duplicate",
              checksum: "matching-content",
            },
          };
        });

        await page.goto(url);
        const titles = page.getByRole("heading", { level: 2 });
        const expected = ["Existing document", "Unrelated document"];

        assert.deepEqual(await titles.allTextContents(), expected);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        assert.deepEqual(
          await titles.allTextContents(),
          expected,
          "Uploading matching content must preserve both documents without adding a duplicate"
        );

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        assert.deepEqual(
          await titles.allTextContents(),
          expected,
          "Repeated duplicate uploads must leave both documents intact"
        );

        await page.reload();
        assert.deepEqual(
          await titles.allTextContents(),
          expected,
          "Both preserved documents must remain after reloading"
        );
      },
    },
  ],
};
