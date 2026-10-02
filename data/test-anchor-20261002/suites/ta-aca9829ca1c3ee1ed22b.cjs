module.exports = {
  tests: [
    {
      name: "Profile shows the username and only their authored articles",
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
          ["Alice's first article", "Alice's second article"]
        );
        assert.ok(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible());
        assert.ok(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible());
      },
    },
    {
      name: "Direct profile URLs select the requested author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Bobby's article", author: { username: "bobby" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob's article"]
        );
      },
    },
    {
      name: "Favorites show articles favorited by the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's unstarred article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Alice's favorite of Bob", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Bobby's favorite", author: { username: "carol" }, favoritedBy: ["bobby"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's favorite of Bob", "Bob's own favorite"]
        );
        await page.reload();
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's favorite of Bob", "Bob's own favorite"]
        );
      },
    },
    {
      name: "Profile navigation preserves the selected username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored this", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Bob favorited this", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        await Promise.all([
          page.waitForURL(
            target => target.pathname === "/profile/bob/favorites",
            { timeout: 4000 }
          ),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob favorited this"]
        );
        await Promise.all([
          page.waitForURL(
            target => target.pathname === "/profile/bob",
            { timeout: 4000 }
          ),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob authored this"]
        );
      },
    },
    {
      name: "Profiles with no matching articles show no unrelated articles",
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
          assert.equal(await page.getByRole("heading", { level: 2 }).count(), 0);
          assert.ok(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible());
          assert.ok(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible());
        }
      },
    },
  ],
};
