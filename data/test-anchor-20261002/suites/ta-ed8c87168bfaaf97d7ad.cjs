module.exports = {
  tests: [
    {
      name: "Profile lists only articles authored by the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's second article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Bobby's article", author: { username: "bobby" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href, { waitUntil: "domcontentloaded", timeout: 8000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Favorites lists articles favorited by the profile user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's saved article", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 2, title: "Shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob's unsaved article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Bobby's favorite", author: { username: "carol" }, favoritedBy: ["bobby"] },
              { id: 5, title: "Nobody's favorite", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob/favorites", url).href, { waitUntil: "domcontentloaded", timeout: 8000 });

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's saved article", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Article tabs preserve the profile username and switch the displayed list",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Carol", author: { username: "carol" }, favoritedBy: [] },
              { id: 2, title: "Saved by Carol", author: { username: "bob" }, favoritedBy: ["carol"] },
              { id: 3, title: "Unrelated article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/carol", url).href, { waitUntil: "domcontentloaded", timeout: 5000 });
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Carol"]);

        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForURL("**/profile/carol/favorites", { waitUntil: "domcontentloaded", timeout: 3000 });
        await page.getByRole("heading", { name: "Saved by Carol", exact: true }).waitFor({ timeout: 3000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Saved by Carol"]);

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForURL("**/profile/carol", { waitUntil: "domcontentloaded", timeout: 3000 });
        await page.getByRole("heading", { name: "Written by Carol", exact: true }).waitFor({ timeout: 3000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Carol"]);
      },
    },
    {
      name: "Profiles with no matching articles show neither other users' articles nor favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        for (const path of ["/profile/dana", "/profile/dana/favorites"]) {
          await page.goto(new URL(path, url).href, { waitUntil: "domcontentloaded", timeout: 5000 });
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "dana");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
