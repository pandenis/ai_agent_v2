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

  it('test_deploy_button_visible_when_model_selected', async () => {
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
    fireEvent.click(screen.getAllByText('mistral')[0]);

    await waitFor(() => {
      expect(screen.getByText('🚀 Deploy')).toBeTruthy();
    });
  });

  it('test_deploy_button_calls_post_api', async () => {
    const mockFetch = vi.fn((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        return Promise.resolve({
          json: () => Promise.resolve({ success: true, output: 'model created', name: 'mistral:latest' }),
        });
      }
      if (url === '/api/v1/models') {
        return Promise.resolve({
          json: () => Promise.resolve({ models: [{ name: 'mistral:latest' }] }),
        });
      }
      return Promise.resolve({
        json: () => Promise.resolve({ modelfile: 'FROM mistral' }),
      });
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<ModelsModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('mistral')).toBeTruthy());
    fireEvent.click(screen.getAllByText('mistral')[0]);
    await waitFor(() => expect(screen.getByText('🚀 Deploy')).toBeTruthy());
    fireEvent.click(screen.getByText('🚀 Deploy'));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/models', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'mistral:latest', modelfile: 'FROM mistral' }),
      }));
    });
  });

  it('test_deploy_success_shows_output', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        return Promise.resolve({
          json: () => Promise.resolve({ success: true, output: 'model created', name: 'mistral:latest' }),
        });
      }
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
    fireEvent.click(screen.getAllByText('mistral')[0]);
    await waitFor(() => expect(screen.getByText('🚀 Deploy')).toBeTruthy());
    fireEvent.click(screen.getByText('🚀 Deploy'));

    await waitFor(() => {
      expect(screen.getByTestId('deploy-output').textContent).toContain('✅ Success');
    });
  });

  it('test_deploy_error_shows_error_message', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        return Promise.reject(new Error('connection refused'));
      }
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
    fireEvent.click(screen.getAllByText('mistral')[0]);
    await waitFor(() => expect(screen.getByText('🚀 Deploy')).toBeTruthy());
    fireEvent.click(screen.getByText('🚀 Deploy'));

    await waitFor(() => {
      expect(screen.getByTestId('deploy-output').textContent).toContain('❌ Error');
    });
  });

  it('test_deploy_button_disabled_while_deploying', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        return new Promise(() => {}); // never resolves
      }
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
    fireEvent.click(screen.getAllByText('mistral')[0]);
    await waitFor(() => expect(screen.getByText('🚀 Deploy')).toBeTruthy());
    fireEvent.click(screen.getByText('🚀 Deploy'));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: 'Deploying...' });
      expect(btn).toBeDisabled();
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
