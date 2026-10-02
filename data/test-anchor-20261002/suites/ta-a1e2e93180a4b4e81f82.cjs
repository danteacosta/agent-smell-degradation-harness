module.exports = {
  tests: [
    {
      name: "Saving edits persists both work values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("20");
        await remaining.fill("7");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await page.getByRole("status").textContent(), "Saved.");
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "7");

        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "7");
      },
    },
    {
      name: "Remaining work equal to Work, including zero, can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        for (const value of ["6", "0"]) {
          await work.fill(value);
          await remaining.fill(value);
          await page.getByRole("button", { name: "Save", exact: true }).click();

          assert.equal(await page.getByRole("status").textContent(), "Saved.");
          await page.reload();
          assert.equal(await work.inputValue(), value);
          assert.equal(await remaining.inputValue(), value);
        }
      },
    },
    {
      name: "Excess remaining work is rejected and corrected edits can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("8");
        await remaining.fill("3");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved.");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work."
        );

        await page.reload();
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "3");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work."
        );

        await remaining.fill("5");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved.");

        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "5");
      },
    },
    {
      name: "Reducing Work below unchanged Remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("6");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved.");

        await work.fill("5");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work."
        );

        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
