import {test, expect, type Page} from '@playwright/test';

const emptyBoard = {items: [], total: 0, next_offset: null, points_per_approval: 20};
const rankedBoard = {
 items: [{handle: 'synthetic-contributor', total_points: 40, approved_contributions: 2, rank: 1}],
 total: 1, next_offset: null, points_per_approval: 20
};
const timeoutMessage = 'The server took too long to respond. Please try again.';

async function expectEmptyBoard(page: Page) {
 await expect(page.getByText('0 contributors', {exact: true})).toBeVisible();
 await expect(page.getByRole('heading', {name: 'The first good start could be yours.'})).toBeVisible();
 await expect(page.getByText('Loading public ranks…', {exact: true})).toHaveCount(0);
}

test.beforeEach(async ({page}) => {
 await page.clock.install();
 await page.route('**/v1/auth/session', route => route.fulfill({status: 401, json: {code: 'auth_required'}}));
});

test('LL-01/02/07: stalled leaderboard times out and Retry loads real ranks', async ({page}) => {
 let requests = 0;
 const aborted: string[] = [];
 page.on('requestfailed', request => {
  if (request.url().includes('/v1/leaderboard')) aborted.push(request.failure()?.errorText ?? '');
 });
 await page.route('**/v1/leaderboard*', route => {
  requests++;
  // Leaving the first request pending reproduces a server that never sends headers.
  if (requests > 1) return route.fulfill({json: rankedBoard});
 });
 await page.goto('/#leaderboard');
 await expect.poll(() => requests).toBe(1);
 await expect(page.getByRole('status')).toHaveText('Loading public ranks…');
 await page.clock.runFor(9_000);
 await expect(page.getByRole('status')).toHaveText('Loading public ranks…');
 await page.clock.runFor(1_100);
 await expect(page.getByRole('alert')).toContainText(timeoutMessage);
 await expect.poll(() => aborted).toEqual(['net::ERR_ABORTED']);
 await expect(page.getByRole('heading', {name: 'The first good start could be yours.'})).toHaveCount(0);
 await page.getByRole('button', {name: 'Retry leaderboard', exact: true}).click();
 await expect(page.getByRole('table').getByRole('row')).toHaveCount(2);
 const member = page.getByRole('row').filter({hasText: '@synthetic-contributor'});
 await expect(member.getByRole('cell').nth(0)).toHaveText('1');
 await expect(member.getByRole('cell').nth(2)).toHaveText('2');
 await expect(member.getByRole('cell').nth(3)).toContainText('40');
 expect(requests).toBe(2);
 await page.clock.runFor(20_000);
 await expect(member).toBeVisible();
 await expect(page.getByRole('alert')).toHaveCount(0);
});

test('LL-03: a stalled session lookup cannot keep the public board opening forever', async ({page}) => {
 let sessionRequests = 0;
 await page.route('**/v1/auth/session', () => {sessionRequests++;});
 await page.route('**/v1/leaderboard*', route => route.fulfill({json: emptyBoard}));
 await page.goto('/#leaderboard');
 await expect.poll(() => sessionRequests).toBe(1);
 await expect(page.getByRole('heading', {name: 'Leaderboard.', exact: true})).toHaveCount(0);
 await page.clock.runFor(10_100);
 await expectEmptyBoard(page);
 await expect(page.getByRole('button', {name: 'Create your free account →', exact: true})).toBeVisible();
 await expect(page.getByRole('button', {name: 'Sign out', exact: true})).toHaveCount(0);
});

test('LL-04: a successful empty response shows zero contributors', async ({page}) => {
 await page.route('**/v1/leaderboard*', route => route.fulfill({json: emptyBoard}));
 await page.goto('/#leaderboard');
 await expectEmptyBoard(page);
 await page.clock.runFor(20_000);
 await expectEmptyBoard(page);
 await expect(page.getByRole('alert')).toHaveCount(0);
});

test('LL-05: server errors remain errors until Retry succeeds', async ({page}) => {
 let requests = 0;
 await page.route('**/v1/leaderboard*', route => {
  requests++;
  return requests === 1
   ? route.fulfill({status: 503, json: {code: 'server_unavailable'}})
   : route.fulfill({json: emptyBoard});
 });
 await page.goto('/#leaderboard');
 await expect(page.getByRole('alert')).toContainText('Cannot connect to the server.');
 await expect(page.getByRole('heading', {name: 'The first good start could be yours.'})).toHaveCount(0);
 await page.getByRole('button', {name: 'Retry leaderboard', exact: true}).click();
 await expectEmptyBoard(page);
 await expect(page.getByRole('alert')).toHaveCount(0);
 expect(requests).toBe(2);
});

test('LL-06: the deadline also covers a stalled JSON response body', async ({page}) => {
 await page.addInitScript(() => {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, options) => {
   if (!String(input).startsWith('/v1/leaderboard')) return originalFetch(input, options);
   const body = new ReadableStream<Uint8Array>({
    start(controller) {
     controller.enqueue(new TextEncoder().encode('{"items":'));
     options?.signal?.addEventListener('abort', () => {
      controller.error(new DOMException('The response was aborted.', 'AbortError'));
     }, {once: true});
    }
   });
   return Promise.resolve(new Response(body, {headers: {'Content-Type': 'application/json'}}));
  };
 });
 await page.goto('/#leaderboard');
 await expect(page.getByRole('status')).toHaveText('Loading public ranks…');
 await page.clock.runFor(10_100);
 await expect(page.getByRole('alert')).toContainText(timeoutMessage);
 await expect(page.getByRole('button', {name: 'Retry leaderboard', exact: true})).toBeVisible();
});
