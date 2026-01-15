import { MainLayout } from '@/components/layouts/MainLayout';

function Sidebar() {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-border">
        <input
          type="search"
          placeholder="🔍 Search dialogs..."
          className="w-full px-3 py-2 text-sm rounded-md border border-border bg-background"
        />
      </div>
      <div className="p-3">
        <button className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          + New Dialog
        </button>
      </div>
      <div className="flex-1 p-3 text-sm text-muted-foreground">
        Sessions will appear here...
      </div>
    </div>
  );
}

function ChatArea() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="text-center text-muted-foreground py-8">
          Start a conversation...
        </div>
      </div>
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function ContextPanel() {
  return (
    <div className="p-4">
      <h3 className="font-semibold mb-4">Context</h3>
      <div className="text-sm text-muted-foreground">
        Memory and context info will appear here...
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <MainLayout
      sidebar={<Sidebar />}
      contextPanel={<ContextPanel />}
    >
      <ChatArea />
    </MainLayout>
  );
}
