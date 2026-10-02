module.exports = {
  tests: [
    {
      name: "Saving both edits preserves them after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("18");
        await remaining.fill("11");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "18");
        assert.equal(await remaining.inputValue(), "11");

        await page.reload();

        assert.equal(await work.inputValue(), "18");
        assert.equal(await remaining.inputValue(), "11");
      },
    },
    {
      name: "Saving Work alone preserves Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("12.5");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(
          await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(),
          "12.5"
        );
        assert.equal(
          await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(),
          "6"
        );
      },
    },
    {
      name: "Later saves replace Remaining work, including zero",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await remaining.fill("2.5");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "2.5");

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
