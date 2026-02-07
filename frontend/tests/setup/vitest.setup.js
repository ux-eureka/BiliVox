// ResizeObserver polyfill for jsdom
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
if (typeof window !== 'undefined' && typeof window.ResizeObserver === 'undefined') {
  window.ResizeObserver = MockResizeObserver
}
if (typeof global !== 'undefined' && typeof global.ResizeObserver === 'undefined') {
  global.ResizeObserver = MockResizeObserver
}

// scrollTo polyfill
if (typeof window !== 'undefined') {
  if (!Element.prototype.scrollTo) {
    Element.prototype.scrollTo = function (optionsOrX, y) {
      if (typeof optionsOrX === 'object' && optionsOrX) {
        this.scrollTop = optionsOrX.top ?? this.scrollTop
        this.scrollLeft = optionsOrX.left ?? this.scrollLeft
      } else {
        this.scrollLeft = optionsOrX ?? this.scrollLeft
        this.scrollTop = y ?? this.scrollTop
      }
    }
  }
}
