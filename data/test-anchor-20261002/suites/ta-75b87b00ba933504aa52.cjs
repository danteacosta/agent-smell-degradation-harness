module.exports = {
  tests: [
    {
      name: "Profile shows the user and only their authored articles",
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
        assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
      },
    },
    {
      name: "Favorites shows articles favorited by the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's unfavorited article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's favorite of Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice's own favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Unrelated article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "alice");
        const expected = ["Bob's favorite of Alice", "Alice's own favorite"].sort();
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          expected
        );

        await page.reload();
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          expected
        );
      },
    },
    {
      name: "Article tabs preserve another user's profile",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Bob", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Favorited by Bob", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Written by Alice", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Bob"]);

        await Promise.all([
          page.waitForURL(target => target.pathname === "/profile/bob/favorites"),
          page.getByRole("link", { name: "Favorites", exact: true }).click(),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Favorited by Bob"]);

        await Promise.all([
          page.waitForURL(target => target.pathname === "/profile/bob"),
          page.getByRole("link", { name: "My Articles", exact: true }).click(),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Bob"]);
      },
    },
    {
      name: "A user with no matching articles has empty lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).textContent(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
