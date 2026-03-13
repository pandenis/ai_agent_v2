import { render, screen, fireEvent } from '@testing-library/react';
import { ModelsModal } from '../ModelsModal';

describe('ModelsModal', () => {
  it('test_modal_hidden_when_closed', () => {
    const onClose = vi.fn();
    render(<ModelsModal isOpen={false} onClose={onClose} />);
    expect(screen.queryByText('Model Manager')).toBeNull();
  });

  it('test_modal_visible_when_open', () => {
    const onClose = vi.fn();
    render(<ModelsModal isOpen={true} onClose={onClose} />);
    expect(screen.getByText('🤖 Model Manager')).toBeTruthy();
  });

  it('test_close_button_calls_onClose', () => {
    const onClose = vi.fn();
    render(<ModelsModal isOpen={true} onClose={onClose} />);
    fireEvent.click(screen.getByLabelText('Close'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('test_backdrop_click_calls_onClose', () => {
    const onClose = vi.fn();
    const { container } = render(<ModelsModal isOpen={true} onClose={onClose} />);
    // Click the backdrop (outermost div)
    fireEvent.click(container.firstChild as Element);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
