module.exports = {
  tests: [
    {
      name: "Alice's profile shows her name and only her authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored only", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Alice authored and liked", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 3, title: "Bob liked by Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Bob unrelated", author: { username: "bob" }, favoritedBy: ["bob"] }
            ]
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored and liked", "Alice authored only"]
        );

        await page.getByRole("link", { name: "Favorites", exact: true }).click();
        await page.waitForURL(new URL("/profile/alice/favorites", url).href, { timeout: 3000 });
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored and liked", "Bob liked by Alice"]
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click();
        await page.waitForURL(new URL("/profile/alice", url).href, { timeout: 3000 });
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored and liked", "Alice authored only"]
        );
      }
    },
    {
      name: "Favorites opens directly and retains the correct list after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 2, title: "Other author's favorite", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Own unfavorited article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Nobody's favorite", author: { username: "bob" }, favoritedBy: [] }
            ]
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Other author's favorite", "Own favorite"]
        );

        await page.reload();
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Other author's favorite", "Own favorite"]
        );
      }
    },
    {
      name: "Another username shows that user's profile and authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Bob's second article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Carol's article", author: { username: "carol" }, favoritedBy: ["bob"] }
            ]
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"]
        );
      }
    },
    {
      name: "Another user's favorites are selected by that username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice liked by Bob", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Alice's favorite only", author: { username: "carol" }, favoritedBy: ["alice"] },
              { id: 4, title: "Bob authored but not liked", author: { username: "bob" }, favoritedBy: [] }
            ]
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice liked by Bob", "Bob's own favorite"]
        );
      }
    },
    {
      name: "No favorites produces an empty list even when authored articles exist",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob authored", author: { username: "bob" }, favoritedBy: [] }
            ]
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "alice");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
        assert.equal(await page.getByText("Alice authored", { exact: true }).count(), 0);
        assert.equal(await page.getByText("Bob authored", { exact: true }).count(), 0);
      }
    },
    {
      name: "No authored articles does not substitute the user's favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob liked by Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Carol unrelated", author: { username: "carol" }, favoritedBy: [] }
            ]
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal((await page.getByRole("heading", { level: 1 }).innerText()).trim(), "alice");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
        assert.equal(await page.getByText("Bob liked by Alice", { exact: true }).count(), 0);
        assert.equal(await page.getByText("Carol unrelated", { exact: true }).count(), 0);
      }
    }
  ]
};
