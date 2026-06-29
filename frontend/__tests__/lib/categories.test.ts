import { DEFAULT_CATEGORIES, UNCATEGORIZED, suggestCategory } from '@/lib/categories'

describe('suggestCategory', () => {
  it('matches a known merchant case-insensitively', () => {
    expect(suggestCategory('STARBUCKS STORE 1234')).toBe('Dining')
    expect(suggestCategory('whole foods market')).toBe('Groceries')
    expect(suggestCategory('Amazon.com*A1B2C')).toBe('Shopping')
  })

  it('maps streaming services to Subscriptions', () => {
    expect(suggestCategory('NETFLIX.COM')).toBe('Subscriptions')
    expect(suggestCategory('Spotify USA')).toBe('Subscriptions')
  })

  it('returns undefined for an unknown merchant', () => {
    expect(suggestCategory('SOME LOCAL SHOP LLC')).toBeUndefined()
  })

  it('returns undefined for empty or missing input', () => {
    expect(suggestCategory('')).toBeUndefined()
    expect(suggestCategory(undefined)).toBeUndefined()
    expect(suggestCategory(null)).toBeUndefined()
  })

  it('exposes a stable set of default categories', () => {
    expect(DEFAULT_CATEGORIES).toContain('Groceries')
    expect(DEFAULT_CATEGORIES).toContain('Subscriptions')
    expect(UNCATEGORIZED).toBe('Uncategorized')
  })
})
