import { describe, test, expect } from 'vitest';
import { tokens } from '@/lib/design-tokens';

describe('Design Tokens', () => {
  describe('colors', () => {
    test('status colors are defined', () => {
      expect(tokens.colors.status.success).toBe('#4caf50');
      expect(tokens.colors.status.warning).toBe('#ff9800');
      expect(tokens.colors.status.error).toBe('#f44336');
      expect(tokens.colors.status.info).toBe('#2196f3');
    });

    test('background has light and dark variants', () => {
      expect(tokens.colors.background.light).toBe('#ffffff');
      expect(tokens.colors.background.dark).toBeDefined();
      // Dark mode should NOT be pure black (better for OLED)
      expect(tokens.colors.background.dark).not.toBe('#000000');
    });
  });

  describe('spacing', () => {
    test('follows 8px grid system', () => {
      expect(tokens.spacing.sm).toBe('8px');
      expect(tokens.spacing.md).toBe('16px');
      expect(tokens.spacing.lg).toBe('24px');
    });

    test('xs is 4px (half grid)', () => {
      expect(tokens.spacing.xs).toBe('4px');
    });
  });

  describe('layout', () => {
    test('has correct panel widths', () => {
      expect(tokens.layout.sidebarWidth).toBe('250px');
      expect(tokens.layout.contextPanelWidth).toBe('300px');
    });
  });

  describe('typography', () => {
    test('has font families defined', () => {
      expect(tokens.typography.fontFamily.sans).toContain('sans');
      expect(tokens.typography.fontFamily.mono).toContain('mono');
    });
  });
});
