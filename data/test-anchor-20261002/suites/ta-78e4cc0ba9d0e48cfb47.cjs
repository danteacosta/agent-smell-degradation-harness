module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("12");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await page.getByRole("status").textContent(), "Saved.");
        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "12");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "9");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("5");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("5");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await page.getByRole("status").textContent(), "Saved.");
        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "5");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "5");
      },
    },
    {
      name: "Invalid edits leave both previously saved values unchanged",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("15");
        await remaining.fill("6");
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
        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "Lowering Work below Remaining is rejected and can be corrected",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("8");
        await remaining.fill("4");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved.");

        await work.fill("3");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work."
        );

        await page.reload();
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "4");

        await work.fill("3");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work."
        );

        await remaining.fill("0");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved.");

        await page.reload();
        assert.equal(await work.inputValue(), "3");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
