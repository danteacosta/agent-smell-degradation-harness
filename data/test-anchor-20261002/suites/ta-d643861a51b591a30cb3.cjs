module.exports = {
  tests: [
    {
      name: "Profile shows the username and only articles authored by that user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice's second article", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
      },
    },
    {
      name: "The requested username determines whose profile and articles appear",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Bob's second article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Favorites shows articles favorited by the requested user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 2, title: "Shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob's nonfavorite", author: { username: "bob" }, favoritedBy: [] },
              { id: 4, title: "Only Alice's favorite", author: { username: "carol" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's own favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Users can switch between authored articles and favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Authored article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Favorite article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Authored article"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/alice/favorites", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Favorite article"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/alice", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Authored article"]);
      },
    },
    {
      name: "A profile with no matching articles or favorites shows no unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Unrelated article", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByText("Unrelated article", { exact: true }).count(), 0);
        }
      },
    },
  ],
};
