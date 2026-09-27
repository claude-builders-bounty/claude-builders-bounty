const pages = $input.all().map(({ json }) => json);
if (!pages.length || pages.some((page) => !Array.isArray(page.body) || !page.headers)) {
  throw new Error('GitHub activity requires paginated responses with headers');
}
const rows = pages.flatMap((page) => page.body);
const lastPage = pages[pages.length - 1];
const nextPage = /<([^>]+)>;\s*rel="next"/.exec(String(lastPage.headers.link || ''))?.[1];
const coverage = { pages: pages.length, fetched: rows.length, complete: !nextPage };
