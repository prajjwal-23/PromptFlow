/**
 * Login Page
 * 
 * This page handles user authentication and login.
 */
'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '../store/authStore';
import { AuthLayout } from '../components/Auth/AuthLayout';
import { LoginForm } from '../components/Auth/LoginForm';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, user } = useAuthStore();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const redirectUrl = searchParams?.get('redirect') || '/dashboard';
      router.push(redirectUrl);
    }
  }, [isAuthenticated, user, router, searchParams]);

  // If already authenticated, show loading state while redirecting
  if (isAuthenticated && user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <AuthLayout
      title="Sign in to your account"
      subtitle="Welcome back to PromptFlow"
      footerText="Don't have an account?"
      footerLink={{
        text: "Create an account",
        href: "/register"
      }}
    >
      <LoginForm />
    </AuthLayout>
  );
}