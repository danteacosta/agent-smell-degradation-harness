module.exports = {
  tests: [
    {
      name: "Saving both edits preserves Work and Remaining work after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("12.5");
        await remaining.fill("4.5");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "12.5");
        assert.equal(await remaining.inputValue(), "4.5");

        await page.reload();

        assert.equal(await work.inputValue(), "12.5");
        assert.equal(await remaining.inputValue(), "4.5");
      },
    },
    {
      name: "Saving a Work edit preserves unchanged Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const unchangedRemaining = await remaining.inputValue();

        await work.fill("24");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "24");
        assert.equal(await remaining.inputValue(), unchangedRemaining);
      },
    },
    {
      name: "A later save persists zero Remaining work and preserves Work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("18");
        await remaining.fill("3");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "18");
        assert.equal(await remaining.inputValue(), "3");

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "18");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
