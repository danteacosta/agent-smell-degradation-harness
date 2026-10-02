module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("15");
        await remaining.fill("8");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "8");
      },
    },
    {
      name: "Remaining greater than Work is rejected without overwriting saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("6");
        await save.click();

        await work.fill("12");
        await remaining.fill("13");
        await save.click();

        assert.match(
          await page.getByRole("status").innerText(),
          /remaining work cannot be greater than work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "Reducing Work below Remaining is rejected and corrected edits can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("6");
        await save.click();

        await work.fill("5");
        await save.click();
        assert.match(
          await page.getByRole("status").innerText(),
          /remaining work cannot be greater than work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("5");
        await save.click();
        await remaining.fill("3");
        await save.click();

        await page.reload();
        assert.equal(await work.inputValue(), "5");
        assert.equal(await remaining.inputValue(), "3");
      },
    },
    {
      name: "Equal Work and Remaining values, including zero, can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        for (const value of ["7", "0"]) {
          await work.fill(value);
          await remaining.fill(value);
          await save.click();
          await page.reload();

          assert.equal(await work.inputValue(), value);
          assert.equal(await remaining.inputValue(), value);
        }
      },
    },
  ],
};
