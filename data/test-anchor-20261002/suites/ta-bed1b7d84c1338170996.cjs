module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "15" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("12");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
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

        await work.fill("15");
        await remaining.fill("6");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "6");
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

        for (const value of ["8", "0"]) {
          await work.fill(value);
          await remaining.fill(value);
          await page.getByRole("button", { name: "Save", exact: true }).click();
          await page.reload();

          assert.equal(await work.inputValue(), value);
          assert.equal(await remaining.inputValue(), value);
        }
      },
    },
    {
      name: "Lowering Work below Remaining is rejected and can be corrected",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "8" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await save.click();
        await work.fill("7");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "8");

        await work.fill("7");
        await save.click();
        await remaining.fill("6");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "7");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
