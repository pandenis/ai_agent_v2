'use client';

import { useState } from 'react';
import { MainLayout } from '@/components/layouts/MainLayout';
import { ChatArea } from '@/components/features/ChatArea';
import { SessionList } from '@/components/features/SessionList';
import { ContextPanel } from '@/components/features/ContextPanel';
import { ModelsModal } from '@/components/features/ModelsModal';

export default function Home() {
  const [modelsOpen, setModelsOpen] = useState(false);

  return (
    <>
      <MainLayout
        sidebar={<SessionList onModelsOpen={() => setModelsOpen(true)} />}
        contextPanel={<ContextPanel />}
      >
        <ChatArea />
      </MainLayout>
      <ModelsModal isOpen={modelsOpen} onClose={() => setModelsOpen(false)} />
    </>
  );
}
