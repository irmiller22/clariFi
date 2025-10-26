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

// Mock window.matchMedia
const mockMatchMedia = jest.fn()
global.window.matchMedia = mockMatchMedia

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

  it('initializes with stored theme from localStorage', () => {
    mockLocalStorage.getItem.mockReturnValue('dark')
    
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('dark')
    expect(mockLocalStorage.getItem).toHaveBeenCalledWith('theme')
  })

  it('initializes with system preference when no stored theme', () => {
    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    })
    
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('dark')
  })

  it('toggles theme from light to dark', () => {
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('light')
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('dark')
  })

  it('toggles theme from dark to light', () => {
    mockLocalStorage.getItem.mockReturnValue('dark')
    
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('dark')
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('light')
  })

  it('sets theme directly', () => {
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.setTheme('dark')
    })
    
    expect(result.current.theme).toBe('dark')
  })

  it('adds dark class to document element when theme is dark', () => {
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.setTheme('dark')
    })
    
    expect(mockDocumentElement.classList.add).toHaveBeenCalledWith('dark')
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
  })

  it('removes dark class from document element when theme is light', () => {
    mockLocalStorage.getItem.mockReturnValue('dark')
    
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.setTheme('light')
    })
    
    expect(mockDocumentElement.classList.remove).toHaveBeenCalledWith('dark')
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'light')
  })

  it('persists theme changes to localStorage', () => {
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'light')
  })

  it('handles system preference changes', () => {
    // Simulate no stored preference but system prefers dark
    mockLocalStorage.getItem.mockReturnValue(null)
    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    })
    
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('dark')
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
  })

  it('prefers stored theme over system preference', () => {
    // System prefers dark but user has stored light
    mockLocalStorage.getItem.mockReturnValue('light')
    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    })
    
    const { result } = renderHook(() => useTheme())
    
    expect(result.current.theme).toBe('light')
  })
})