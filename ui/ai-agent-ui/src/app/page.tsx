import { MainLayout } from '@/components/layouts/MainLayout';
import { ChatArea } from '@/components/features/ChatArea';
import { SessionList } from '@/components/features/SessionList';
import { ContextPanel } from '@/components/features/ContextPanel';

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
