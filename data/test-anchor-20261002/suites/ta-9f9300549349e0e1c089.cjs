module.exports = {
  tests: [
    {
      name: "Profile shows the requested user and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob first", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Carol first", author: { username: "carol" }, favoritedBy: ["alice", "bob"] }
            ]
          };
        });

        for (const [username, titles] of [
          ["alice", ["Alice first", "Alice second"]],
          ["bob", ["Bob first"]]
        ]) {
          await page.goto(new URL(`/profile/${username}`, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), username);
          assert.deepEqual(
            (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
            titles.sort()
          );
        }
      }
    },
    {
      name: "Favorites shows articles favorited by the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored only", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob authored only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Shared favorite", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Alice self favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 5, title: "Unfavorited", author: { username: "carol" }, favoritedBy: [] }
            ]
          };
        });

        for (const [username, titles] of [
          ["alice", ["Bob authored only", "Shared favorite", "Alice self favorite"]],
          ["bob", ["Alice authored only", "Shared favorite"]]
        ]) {
          await page.goto(new URL(`/profile/${username}/favorites`, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), username);
          assert.deepEqual(
            (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
            titles.sort()
          );
        }
      }
    },
    {
      name: "Profile navigation preserves the viewed username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob article", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Bob favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice article", author: { username: "alice" }, favoritedBy: ["alice"] }
            ]
          };
        });

        await page.goto(new URL("/profile/bob", url).href);
        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        assert.equal(new URL(page.url()).pathname, "/profile/bob/favorites");
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob favorite"]
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        assert.equal(new URL(page.url()).pathname, "/profile/bob");
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob article"]
        );
      }
    },
    {
      name: "Empty authored and favorites lists do not show unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] }
            ]
          };
        });

        for (const [path, username] of [
          ["/profile/bob", "bob"],
          ["/profile/alice/favorites", "alice"]
        ]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), username);
          assert.deepEqual(
            await page.getByRole("heading", { level: 2 }).allTextContents(),
            []
          );
          assert.equal(await page.getByText("Alice article", { exact: true }).count(), 0);
        }
      }
    }
  ]
};
