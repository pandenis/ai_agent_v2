import { MainLayout } from '@/components/layouts/MainLayout';
import { ChatArea } from '@/components/features/ChatArea';
import { SessionList } from '@/components/features/SessionList';

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
      sidebar={<SessionList />}
      contextPanel={<ContextPanel />}
    >
      <ChatArea />
    </MainLayout>
  );
}
