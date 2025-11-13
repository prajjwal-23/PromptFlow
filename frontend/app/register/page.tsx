/**
 * Register Page
 * 
 * This page handles user registration and account creation.
 */
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../store/authStore';
import { AuthLayout } from '../components/Auth/AuthLayout';
import { RegisterForm } from '../components/Auth/RegisterForm';

export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, user, router]);

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
      title="Create your account"
      subtitle="Join PromptFlow to start building AI agents"
      footerText="Already have an account?"
      footerLink={{
        text: "Sign in",
        href: "/login"
      }}
    >
      <RegisterForm />
    </AuthLayout>
  );
}