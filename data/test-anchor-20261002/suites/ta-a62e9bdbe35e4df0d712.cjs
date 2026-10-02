module.exports = {
  tests: [
    {
      name: "Profile shows the username and only authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Alice favorite only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice authored and favorited", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 4, title: "Unrelated", author: { username: "carol" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        await page.waitForFunction(() => document.querySelectorAll("#articles .article").length === 2, { }, { timeout: 4000 });
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Alice authored", "Alice authored and favorited"].sort()
        );
      },
    },
    {
      name: "Direct favorites URL shows articles favorited by the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Authored only", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Favorite by another author", author: { username: "bob" }, favoritedBy: ["carol", "alice"] },
              { id: 3, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        await page.waitForFunction(() => document.querySelectorAll("#articles .article").length === 2, {}, { timeout: 4000 });
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Favorite by another author", "Own favorite"].sort()
        );
      },
    },
    {
      name: "Profile navigation switches article lists and survives reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Alice", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Saved by Alice", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForFunction(
          () => location.pathname === "/profile/alice/favorites" &&
            document.querySelector("#articles")?.textContent === "Saved by Alice",
          {},
          { timeout: 3000 }
        );
        assert.deepEqual(await page.locator("#articles .article h2").allTextContents(), ["Saved by Alice"]);

        await page.reload();
        await page.waitForFunction(
          () => document.querySelector("#articles")?.textContent === "Saved by Alice",
          {},
          { timeout: 3000 }
        );
        assert.equal(new URL(page.url()).pathname, "/profile/alice/favorites");

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForFunction(
          () => location.pathname === "/profile/alice" &&
            document.querySelector("#articles")?.textContent === "Written by Alice",
          {},
          { timeout: 3000 }
        );
        assert.deepEqual(await page.locator("#articles .article h2").allTextContents(), ["Written by Alice"]);
      },
    },
    {
      name: "Empty favorites do not fall back to authored or unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        await page.waitForFunction(
          () => document.querySelector("#articles .article h2")?.textContent === "Alice article",
          {},
          { timeout: 3000 }
        );
        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForFunction(
          () => location.pathname === "/profile/alice/favorites" &&
            document.querySelectorAll("#articles .article").length === 0,
          {},
          { timeout: 3000 }
        );
        assert.equal(await page.locator("#articles .article").count(), 0);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
      },
    },
    {
      name: "Article filtering uses the username in each profile URL",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob favorited", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice authored", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Similar username", author: { username: "bobby" }, favoritedBy: ["bobby"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        await page.waitForFunction(
          () => document.querySelector("#articles")?.textContent === "Bob authored",
          {},
          { timeout: 3000 }
        );
        assert.deepEqual(await page.locator("#articles .article h2").allTextContents(), ["Bob authored"]);

        await page.goto(new URL("/profile/bob/favorites", url).href);
        await page.waitForFunction(
          () => document.querySelector("#articles")?.textContent === "Bob favorited",
          {},
          { timeout: 3000 }
        );
        assert.deepEqual(await page.locator("#articles .article h2").allTextContents(), ["Bob favorited"]);
      },
    },
  ],
};
