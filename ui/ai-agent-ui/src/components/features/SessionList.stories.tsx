import type { Meta, StoryObj } from '@storybook/react'
import { SessionList } from './SessionList'

const meta: Meta<typeof SessionList> = {
  title: 'Features/SessionList',
  component: SessionList,
}

export default meta
type Story = StoryObj<typeof SessionList>

export const Default: Story = {
  args: {
    currentSessionId: 'abc-123',
    onSessionSelect: (id) => console.log('Selected:', id),
    onNewSession: () => console.log('New session'),
  },
}