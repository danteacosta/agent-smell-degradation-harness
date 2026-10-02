module.exports = {
  tests: [
    {
      name: "Profiles show the requested user and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob first", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Carol first", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
            ],
          };
        });

        for (const [username, expected] of [
          ["alice", ["Alice first", "Alice second"]],
          ["bob", ["Bob first"]],
        ]) {
          await page.goto(new URL(`/profile/${username}`, url).href, { timeout: 5000 });
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), username);
          assert.deepEqual(
            (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
            expected.slice().sort()
          );
        }
      },
    },
    {
      name: "Favorites show articles favorited by the requested user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob favorite of Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Shared favorite", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Only Bob likes this", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 5, title: "Nobody likes this", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });

        for (const [username, expected] of [
          ["alice", ["Alice own favorite", "Bob favorite of Alice", "Shared favorite"]],
          ["bob", ["Shared favorite", "Only Bob likes this"]],
        ]) {
          await page.goto(new URL(`/profile/${username}/favorites`, url).href, { timeout: 5000 });
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), username);
          assert.deepEqual(
            (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
            expected.slice().sort()
          );
        }
      },
    },
    {
      name: "A user with no authored or favorited articles has empty lists",
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
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByText("Another user's article", { exact: true }).count(), 0);
        }
      },
    },
    {
      name: "Switching profile tabs preserves the viewed username and updates articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Bob", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Liked by Bob", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Written by Alice", author: { username: "alice" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href, { timeout: 5000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Bob"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/bob/favorites", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Liked by Bob"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/bob", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Bob"]);
      },
    },
  ],
};
