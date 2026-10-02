module.exports = {
  tests: [
    {
      name: "Saving edits persists both Work and Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("20");
        await remaining.fill("7");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "7");
      },
    },
    {
      name: "Remaining work equal to Work and zero remaining can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("12");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "12");

        await remaining.fill("0");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
    {
      name: "Remaining work above Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("20");
        await remaining.fill("8");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("30");
        await remaining.fill("31");
        if (await save.isEnabled()) await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "8");
      },
    },
    {
      name: "Reducing Work below Remaining work is rejected and can be corrected",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("20");
        await remaining.fill("8");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("7");
        if (await save.isEnabled()) await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("7");
        if (await save.isEnabled()) await save.click();
        await remaining.fill("6");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "7");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
