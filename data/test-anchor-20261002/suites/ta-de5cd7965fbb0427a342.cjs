module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url, { timeout: 5000 });
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("20", { timeout: 2000 });
        await remaining.fill("7", { timeout: 2000 });
        await page.getByRole("button", { name: "Save", exact: true }).click({ timeout: 2000 });

        await page.reload({ timeout: 5000 });
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "7");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url, { timeout: 5000 });
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("8", { timeout: 2000 });
        await remaining.fill("8", { timeout: 2000 });
        await page.getByRole("button", { name: "Save", exact: true }).click({ timeout: 2000 });

        await page.reload({ timeout: 5000 });
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "8");
      },
    },
    {
      name: "Excess Remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url, { timeout: 5000 });
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await save.click({ timeout: 2000 });
        await work.fill("9", { timeout: 2000 });
        await remaining.fill("10", { timeout: 2000 });
        await save.click({ timeout: 2000 });

        await page.reload({ timeout: 5000 });
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Lowering Work below Remaining work is rejected and can be corrected",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url, { timeout: 5000 });
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await save.click({ timeout: 1000 });
        await work.fill("3", { timeout: 1000 });
        await save.click({ timeout: 1000 });

        await page.reload({ timeout: 4000 });
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "4");

        await work.fill("3", { timeout: 1000 });
        await remaining.fill("2", { timeout: 1000 });
        await save.click({ timeout: 1000 });

        await page.reload({ timeout: 4000 });
        assert.equal(await work.inputValue(), "3");
        assert.equal(await remaining.inputValue(), "2");
      },
    },
  ],
};
