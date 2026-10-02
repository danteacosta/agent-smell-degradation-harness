module.exports = {
  tests: [
    {
      name: "Profile shows the user's name and only their authored articles",
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

        await page.goto(new URL("/profile/alice", url).href, { timeout: 5000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.locator(".article h2").allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
      },
    },
    {
      name: "Favorites lists articles favorited by the profile user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 3, title: "Own nonfavorite", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Nobody's favorite", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice/favorites", url).href, { timeout: 5000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.locator(".article h2").allTextContents()).sort(),
          ["Own favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Article and favorites navigation stays on the selected user's profile",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Bob", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Liked by Bob", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice only", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href, { timeout: 5000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.locator(".article h2").allTextContents(), ["Written by Bob"]);

        await Promise.all([
          page.waitForURL("**/profile/bob/favorites", { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.locator(".article h2").allTextContents(), ["Liked by Bob"]);

        await Promise.all([
          page.waitForURL("**/profile/bob", { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.locator(".article h2").allTextContents(), ["Written by Bob"]);
      },
    },
    {
      name: "Users without matching articles have empty authored and favorites lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Another user's article", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });

        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href, { timeout: 5000 });
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.locator(".article h2").allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
    {
      name: "Username matching does not include articles belonging to similar usernames",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Similar username", author: { username: "alice2" }, favoritedBy: ["alice2"] },
              { id: 3, title: "Alice favorited", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice", url).href, { timeout: 5000 });
        assert.deepEqual(await page.locator(".article h2").allTextContents(), ["Alice authored"]);

        await page.goto(new URL("/profile/alice/favorites", url).href, { timeout: 5000 });
        assert.deepEqual(await page.locator(".article h2").allTextContents(), ["Alice favorited"]);
      },
    },
  ],
};
