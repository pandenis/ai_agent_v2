'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useEffect, useState } from 'react';

interface MessageContentProps {
  content: string;
}

export function MessageContent({ content }: MessageContentProps) {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'));
    
    // Watch for theme changes
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    
    return () => observer.disconnect();
  }, []);

  // Parse content for code blocks
  const renderContent = () => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match;
    let key = 0;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push(
          <span key={key++} className="whitespace-pre-wrap">
            {content.slice(lastIndex, match.index)}
          </span>
        );
      }

      // Add code block with syntax highlighting
      const language = match[1] || 'text';
      const code = match[2].trim();
      
      parts.push(
        <div key={key++} className="my-2 rounded-lg overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1 bg-muted/50 text-xs text-muted-foreground">
            <span>{language}</span>
            <button
              onClick={() => navigator.clipboard.writeText(code)}
              className="hover:text-foreground transition-colors"
              title="Copy code"
            >
              📋 Copy
            </button>
          </div>
          <SyntaxHighlighter
            language={language}
            style={isDark ? oneDark : oneLight}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: '13px',
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after last code block
    if (lastIndex < content.length) {
      parts.push(
        <span key={key++} className="whitespace-pre-wrap">
          {content.slice(lastIndex)}
        </span>
      );
    }

    return parts.length > 0 ? parts : <span className="whitespace-pre-wrap">{content}</span>;
  };

  return <div className="text-sm">{renderContent()}</div>;
}
