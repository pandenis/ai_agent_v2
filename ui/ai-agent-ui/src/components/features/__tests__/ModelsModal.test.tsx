import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ModelsModal } from '../ModelsModal';

vi.mock('@uiw/react-codemirror', () => ({
  default: ({ value }: { value: string }) => (
    <textarea data-testid="codemirror-editor" defaultValue={value} />
  ),
}));

const EMPTY_FETCH = vi.fn().mockResolvedValue({
  json: () => Promise.resolve({ models: [] }),
});

const MODEL_FETCH = vi.fn().mockResolvedValue({
  json: () =>
    Promise.resolve({
      models: [{ name: 'mistral:latest' }, { name: 'deepseek-coder:latest' }],
    }),
});

beforeEach(() => {
  vi.stubGlobal('fetch', EMPTY_FETCH);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

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
    fireEvent.click(container.firstChild as Element);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('test_shows_loading_while_fetching', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Loading...')).toBeTruthy();
  });

  it('test_shows_model_list_after_fetch', async () => {
    vi.stubGlobal('fetch', MODEL_FETCH);
    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('mistral')).toBeTruthy();
      expect(screen.getByText('deepseek-coder')).toBeTruthy();
    });
  });

  it('test_selecting_model_highlights_it', async () => {
    vi.stubGlobal('fetch', MODEL_FETCH);
    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    fireEvent.click(screen.getAllByText('mistral')[0]);
    expect(screen.getAllByText('mistral')[0].className).toContain('bg-slate-600');
  });

  it('test_right_panel_shows_prompt_when_nothing_selected', async () => {
    vi.stubGlobal('fetch', MODEL_FETCH);
    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    expect(screen.getByText('Select a model to view its Modelfile')).toBeTruthy();
  });

  it('test_fetches_modelfile_when_model_selected', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url === '/api/v1/models') {
        return Promise.resolve({
          json: () => Promise.resolve({ models: [{ name: 'mistral:latest' }] }),
        });
      }
      return Promise.resolve({
        json: () => Promise.resolve({ modelfile: 'FROM mistral\nSYSTEM Be helpful' }),
      });
    }));

    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    fireEvent.click(screen.getByText('mistral'));

    await waitFor(() => {
      const editor = screen.getByTestId('codemirror-editor') as HTMLTextAreaElement;
      expect(editor.defaultValue).toContain('FROM mistral');
    });
  });

  it('test_shows_loading_while_fetching_modelfile', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url === '/api/v1/models') {
        return Promise.resolve({
          json: () => Promise.resolve({ models: [{ name: 'mistral:latest' }] }),
        });
      }
      // model detail fetch never resolves → loading stays
      return new Promise(() => {});
    }));

    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    fireEvent.click(screen.getByText('mistral'));

    await waitFor(() => {
      expect(screen.getByText('Loading Modelfile...')).toBeTruthy();
    });
  });

  it('test_editor_updates_on_content_change', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url === '/api/v1/models') {
        return Promise.resolve({
          json: () => Promise.resolve({ models: [{ name: 'mistral:latest' }] }),
        });
      }
      return Promise.resolve({
        json: () => Promise.resolve({ modelfile: 'FROM mistral' }),
      });
    }));

    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    fireEvent.click(screen.getByText('mistral'));

    await waitFor(() =>
      expect(screen.getByTestId('codemirror-editor')).toBeTruthy()
    );

    const editor = screen.getByTestId('codemirror-editor') as HTMLTextAreaElement;
    fireEvent.change(editor, { target: { value: 'FROM mistral\nSYSTEM Updated' } });
    expect(editor.value).toBe('FROM mistral\nSYSTEM Updated');
  });
});
