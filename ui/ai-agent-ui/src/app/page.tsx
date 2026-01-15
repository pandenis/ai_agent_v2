import { MainLayout } from '@/components/layouts/MainLayout';
import { ChatArea } from '@/components/features/ChatArea';

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
