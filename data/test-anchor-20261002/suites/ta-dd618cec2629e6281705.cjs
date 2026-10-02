module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2500);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
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

        await work.fill("6");
        await remaining.fill("2");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "6");
        assert.equal(await remaining.inputValue(), "2");
      },
    },
    {
      name: "Remaining work equal to Work can be saved, including zero",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2500);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "3" };
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
      name: "Increasing Remaining work above Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2500);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("9");
        await remaining.fill("4");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "4");

        await remaining.fill("10");
        await work.focus();
        if (await save.isEnabled()) {
          await save.click();
        }
        await page.reload();

        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Reducing Work below Remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2500);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "3" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("6");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("5");
        await remaining.focus();
        if (await save.isEnabled()) {
          await save.click();
        }
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
