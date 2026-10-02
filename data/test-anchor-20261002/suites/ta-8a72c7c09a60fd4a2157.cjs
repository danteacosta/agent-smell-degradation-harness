module.exports = {
  tests: [
    {
      name: "Profile shows username and only authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second article", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice first article", "Alice second article"]
        );
      },
    },
    {
      name: "Favorites and authored tabs show their respective articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Authored only", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Favorite by Bob", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        await Promise.all([
          page.waitForURL(new URL("/profile/alice/favorites", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Favorite by Bob", "Own favorite"]
        );

        await Promise.all([
          page.waitForURL(new URL("/profile/alice", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Authored only", "Own favorite"]
        );
      },
    },
    {
      name: "Authored profile uses the username in the URL",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Bob second article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob first article", "Bob second article"]
        );
      },
    },
    {
      name: "Direct favorites URL shows the requested user's favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob likes Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob authored only", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Alice likes Carol's article", author: { username: "carol" }, favoritedBy: ["alice"] },
              { id: 4, title: "Shared favorite", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob likes Alice's article", "Shared favorite"]
        );
      },
    },
    {
      name: "Profiles with no matching articles show no unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob article", author: { username: "bob" }, favoritedBy: ["carol"] },
              { id: 2, title: "Carol article", author: { username: "carol" }, favoritedBy: ["bob"] },
            ],
          };
        });
        for (const path of ["/profile/alice", "/profile/alice/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByText("Bob article", { exact: true }).count(), 0);
          assert.equal(await page.getByText("Carol article", { exact: true }).count(), 0);
        }
      },
    },
  ],
};
