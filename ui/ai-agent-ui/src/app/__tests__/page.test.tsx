import { render, screen, fireEvent } from '@testing-library/react';
import Home from '../page';

// Stub out heavy dependencies so page renders in jsdom
vi.mock('@/components/layouts/MainLayout', () => ({
  MainLayout: ({ sidebar, children }: { sidebar: React.ReactNode; children: React.ReactNode }) => (
    <div>
      <div data-testid="sidebar">{sidebar}</div>
      <div>{children}</div>
    </div>
  ),
}));

vi.mock('@/components/features/ChatArea', () => ({
  ChatArea: () => <div />,
}));

vi.mock('@/components/features/ContextPanel', () => ({
  ContextPanel: () => <div />,
}));

vi.mock('@/components/features/SessionList', () => ({
  SessionList: ({ onModelsOpen }: { onModelsOpen?: () => void }) => (
    <button onClick={onModelsOpen}>🤖 Models</button>
  ),
}));

describe('Home page modal wiring', () => {
  it('test_models_button_opens_modal', () => {
    render(<Home />);
    fireEvent.click(screen.getByText('🤖 Models'));
    expect(screen.getByText('🤖 Model Manager')).toBeTruthy();
  });

  it('test_modal_close_hides_modal', () => {
    render(<Home />);
    fireEvent.click(screen.getByText('🤖 Models'));
    expect(screen.getByText('🤖 Model Manager')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Close'));
    expect(screen.queryByText('🤖 Model Manager')).toBeNull();
  });
});
