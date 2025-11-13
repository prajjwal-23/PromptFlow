/**
 * Agent Edit Page
 * 
 * This page redirects to the agent editor.
 */
'use client';

import { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

export default function AgentEditPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;

  useEffect(() => {
    // Redirect to the actual editor page
    router.replace(`/editor/${agentId}`);
  }, [router, agentId]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-2 text-gray-600">Redirecting to editor...</p>
      </div>
    </div>
  );
}