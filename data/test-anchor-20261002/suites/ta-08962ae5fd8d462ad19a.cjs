module.exports = {
  tests: [
    {
      name: "Profile shows the username and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
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
      name: "Favorites show articles favorited by the profile user and tabs navigate correctly",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored only", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob favorited by Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice self favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Unrelated article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        const favorites = ["Alice self favorite", "Bob favorited by Alice"];
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          favorites
        );

        await Promise.all([
          page.waitForURL(new URL("/profile/alice", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored only", "Alice self favorite"]
        );

        await Promise.all([
          page.waitForURL(new URL("/profile/alice/favorites", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          favorites
        );
      },
    },
    {
      name: "A different username selects that user's profile and authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
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
      name: "A different user's favorites are selected independently of authorship",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob favorite by Alice", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob authored only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Shared favorite", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Nobody's favorite", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob favorite by Alice", "Shared favorite"]
        );
      },
    },
    {
      name: "Profiles with no matching articles do not show other users' articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob article", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 2, title: "Carol article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        for (const path of ["/profile/alice", "/profile/alice/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
          assert.deepEqual(
            await page.getByRole("heading", { level: 2 }).allTextContents(),
            []
          );
        }
      },
    },
  ],
};
