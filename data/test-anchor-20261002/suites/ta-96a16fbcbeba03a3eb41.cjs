module.exports = {
  tests: [
    {
      name: "Profile shows the username and only that user's articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob's article liked by Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice's second article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Similar username's article", author: { username: "alice2" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
        assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
        assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
      },
    },
    {
      name: "Direct profile URLs select the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice writes", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob writes", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob writes"]);

        await page.reload();
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob writes"]);
      },
    },
    {
      name: "Favorites and authored navigation preserve the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's unfavorited article", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Alice's article Bob likes", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's article Bob likes", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 4, title: "Only Alice likes this", author: { username: "carol" }, favoritedBy: ["alice"] },
            ],
          };
        });

        const authoredUrl = new URL("/profile/bob", url).href;
        const favoritesUrl = new URL("/profile/bob/favorites", url).href;
        await page.goto(favoritesUrl);

        const checkFavorites = async () => {
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
          assert.deepEqual(
            (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
            ["Alice's article Bob likes", "Bob's article Bob likes"].sort()
          );
        };
        await checkFavorites();

        await Promise.all([
          page.waitForURL(authoredUrl, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's unfavorited article", "Bob's article Bob likes"].sort()
        );

        await Promise.all([
          page.waitForURL(favoritesUrl, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        await checkFavorites();
      },
    },
    {
      name: "Profiles with no matching articles show no unrelated articles",
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
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByText("Alice's article", { exact: true }).count(), 0);
          assert.equal(await page.getByText("Bob's article", { exact: true }).count(), 0);
        }
      },
    },
    {
      name: "An empty article collection still displays the profile and navigation",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { articles: [] };
        });

        for (const path of ["/profile/alice", "/profile/alice/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
