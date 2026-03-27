/**
 * Upper bound for `page_size` on paginated list APIs (`/members`, `/ministries`, `/events`, etc.).
 * Must stay aligned with backend `Query(..., le=_MAX_PAGE_SIZE)` (currently 100 per router).
 */
export const API_MAX_PAGE_SIZE = 100;

/**
 * Fetches every page of a list endpoint until `items.length >= total`, using at most
 * `API_MAX_PAGE_SIZE` per request so responses stay within backend validation.
 */
export async function fetchAllListPages<TItem>(options: {
  fetchPage: (page: number, pageSize: number) => Promise<{
    items: TItem[];
    total: number;
  }>;
  pageSize?: number;
}): Promise<TItem[]> {
  const pageSize = Math.min(options.pageSize ?? API_MAX_PAGE_SIZE, API_MAX_PAGE_SIZE);
  const out: TItem[] = [];
  let page = 1;
  let total = Infinity;

  while (out.length < total) {
    const res = await options.fetchPage(page, pageSize);
    total = res.total;
    out.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return out;
}
