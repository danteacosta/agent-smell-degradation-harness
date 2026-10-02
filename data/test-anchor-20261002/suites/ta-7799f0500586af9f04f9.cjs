module.exports = {
  tests: [
    {
      name: "Profile shows username and only articles authored by that user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Unrelated article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice", url).href);
        await page.getByRole("heading", { level: 1 }).waitFor({ timeout: 5000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice first article", "Alice second article"].sort()
        );
      },
    },
    {
      name: "Favorites lists favorited articles regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["carol", "alice"] },
              { id: 3, title: "Authored but not favorited", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 5, title: "Nobody's favorite", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice/favorites", url).href);
        await page.getByRole("heading", { level: 1 }).waitFor({ timeout: 5000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice own favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Switching profile tabs preserves the selected user and survives reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob favorited", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice authored", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob authored"]);

        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 });
        await page.waitForURL(new URL("/profile/bob/favorites", url).href, { timeout: 5000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob favorited"]);

        await page.reload();
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob favorited"]);

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 });
        await page.waitForURL(new URL("/profile/bob", url).href, { timeout: 5000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob authored"]);
      },
    },
    {
      name: "A user with no authored or favorited articles sees no unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          await page.getByRole("heading", { level: 1 }).waitFor({ timeout: 5000 });

          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
