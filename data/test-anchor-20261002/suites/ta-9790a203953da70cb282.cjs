module.exports = {
  tests: [
    {
      name: "Saving edits persists both Work and Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("12");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click({ timeout: 2000 });

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");

        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "2" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("6");
        await remaining.fill("6");
        await page.getByRole("button", { name: "Save", exact: true }).click({ timeout: 2000 });

        await page.reload();
        assert.equal(await work.inputValue(), "6");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "Increasing Remaining work above Work preserves the last saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "15", remaining: "3" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("8");
        await remaining.fill("4");
        await save.click({ timeout: 2000 });
        await page.reload();
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "4");

        await work.fill("9");
        await remaining.fill("10");
        await remaining.blur();
        if (await save.isEnabled()) {
          await save.click({ timeout: 2000 });
        }

        await page.reload();
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Lowering Work below Remaining work is rejected and can be corrected",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("8");
        await save.click({ timeout: 2000 });
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("7");
        await work.blur();
        if (await save.isEnabled()) {
          await save.click({ timeout: 2000 });
        }

        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("7");
        await remaining.fill("6");
        await save.click({ timeout: 2000 });

        await page.reload();
        assert.equal(await work.inputValue(), "7");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
