module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("10");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Remaining greater than Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("4");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "4");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Remaining equal to Work can be saved, including zero",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        for (const value of ["7", "0"]) {
          await work.fill(value);
          await remaining.fill(value);
          await page.getByRole("button", { name: "Save", exact: true }).click();
          await page.reload();

          assert.equal(await work.inputValue(), value);
          assert.equal(await remaining.inputValue(), value);
        }
      },
    },
  ],
};
