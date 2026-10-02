module.exports = {
  tests: [
    {
      name: "Saving both edits preserves them after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("4");
        await save.click();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "4");

        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Editing either value preserves the other saved value",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "7" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("7");
        await save.click();

        await work.fill("15");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "7");

        await remaining.fill("3");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "3");
      },
    },
    {
      name: "Later saves replace earlier values including zero remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("4");
        await save.click();

        await work.fill("12.5");
        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12.5");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
