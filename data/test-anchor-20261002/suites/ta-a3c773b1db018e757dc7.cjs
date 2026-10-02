module.exports = {
  tests: [
    {
      name: "Saving both edits preserves them after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "8" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("20");
        await remaining.fill("15");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "15");

        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "15");

        await work.fill("24");
        await remaining.fill("10");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "24");
        assert.equal(await remaining.inputValue(), "10");
      },
    },
    {
      name: "Saving Work alone preserves Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "8" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("18");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(
          await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(),
          "18"
        );
        assert.equal(
          await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(),
          "8"
        );
      },
    },
    {
      name: "Saving zero Remaining work preserves Work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "8" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("0");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(
          await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(),
          "12"
        );
        assert.equal(
          await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(),
          "0"
        );
      },
    },
  ],
};
