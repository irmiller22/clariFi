import { renderHook, act } from '@testing-library/react'
import { useTheme } from '@/hooks/use-theme'

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = mockLocalStorage as any

// Mock window.matchMedia
const mockMatchMedia = jest.fn()
global.window.matchMedia = mockMatchMedia

// Mock document.documentElement
const mockDocumentElement = {
  classList: {
    add: jest.fn(),
    remove: jest.fn(),
    contains: jest.fn(),
  }
}

Object.defineProperty(document, 'documentElement', {
  value: mockDocumentElement,
  writable: true
})

describe('useTheme Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    })
  })

  it('initializes with light theme by default', () => {
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('light')
  })

  it('provides theme toggle functionality', () => {
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('light')
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('dark')
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('light')
  })

  it('provides setTheme functionality', () => {
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.setTheme('dark')
    })
    
    expect(result.current.theme).toBe('dark')
    
    act(() => {
      result.current.setTheme('light')
    })
    
    expect(result.current.theme).toBe('light')
  })

  it('returns the correct API shape', () => {
    const { result } = renderHook(() => useTheme())
    
    expect(typeof result.current.theme).toBe('string')
    expect(typeof result.current.toggleTheme).toBe('function')
    expect(typeof result.current.setTheme).toBe('function')
    
    expect(['light', 'dark']).toContain(result.current.theme)
  })
})