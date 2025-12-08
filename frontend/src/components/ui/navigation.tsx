'use client';
import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Menu, X, Brain } from 'lucide-react'
import { Button } from '@/src/components/ui/button'
import { cn } from '@/src/lib/utils'
import { useAuthStore } from '@/src/store/authStore'

interface NavigationProps {
  variant?: 'hero' | 'dashboard' | 'minimal'
  className?: string
}

const menuItems = [
    { name: 'Agents', href: '/agents' },
    { name: 'Workspaces', href: '/workspaces' },
    { name: 'Runs', href: '/runs' },
    { name: 'Dashboard', href: '/dashboard' },
]

const Logo = ({ className }: { className?: string }) => {
    return (
        <div className={cn('flex items-center space-x-2', className)}>
            <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-black" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-500 bg-clip-text text-transparent">
                PromptFlow
            </span>
        </div>
    )
}

export function Navigation({ variant = 'hero', className }: NavigationProps) {
    const [menuState, setMenuState] = React.useState(false)
    const [isScrolled, setIsScrolled] = React.useState(false)
    const { isAuthenticated, user, logout } = useAuthStore()
    const router = useRouter()

    React.useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    const handleLogin = () => {
        router.push('/login')
    }

    const handleSignup = () => {
        router.push('/register')
    }

    const handleLogout = async () => {
        await logout()
        router.push('/')
    }

    const handleProfile = () => {
        router.push('/profile')
    }

    const handleDashboard = () => {
        router.push('/dashboard')
    }

    const getNavStyles = () => {
        switch (variant) {
            case 'hero':
                return cn(
                    'fixed z-20 w-full px-2 group',
                    isScrolled && 'bg-background/50 backdrop-blur-lg'
                )
            case 'dashboard':
                return cn(
                    'sticky top-0 z-20 w-full bg-background/80 backdrop-blur-lg border-b'
                )
            case 'minimal':
                return cn(
                    'fixed z-20 w-full bg-background border-b'
                )
            default:
                return cn(
                    'fixed z-20 w-full px-2 group',
                    isScrolled && 'bg-background/50 backdrop-blur-lg'
                )
        }
    }

    const getContainerStyles = () => {
        switch (variant) {
            case 'hero':
                return cn(
                    'mx-auto mt-2 max-w-6xl px-6 transition-all duration-300 lg:px-12',
                    isScrolled && 'max-w-4xl rounded-2xl border lg:px-5'
                )
            case 'dashboard':
                return 'mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'
            case 'minimal':
                return 'mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'
            default:
                return cn(
                    'mx-auto mt-2 max-w-6xl px-6 transition-all duration-300 lg:px-12',
                    isScrolled && 'max-w-4xl rounded-2xl border lg:px-5'
                )
        }
    }

    return (
        <header>
            <nav
                data-state={menuState && 'active'}
                className={getNavStyles()}>
                <div className={getContainerStyles()}>
                    <div className="relative flex flex-wrap items-center justify-between gap-6 py-3 lg:gap-0 lg:py-4">
                        <div className="flex w-full justify-between lg:w-auto">
                            <Link
                                href="/"
                                aria-label="home"
                                className="flex items-center space-x-2">
                                <Logo />
                            </Link>

                            {variant !== 'dashboard' && (
                                <button
                                    onClick={() => setMenuState(!menuState)}
                                    aria-label={menuState == true ? 'Close Menu' : 'Open Menu'}
                                    className="relative z-20 -m-2.5 -mr-4 block cursor-pointer p-2.5 lg:hidden">
                                    <Menu className="in-data-[state=active]:rotate-180 group-data-[state=active]:scale-0 group-data-[state=active]:opacity-0 m-auto size-6 duration-200" />
                                    <X className="group-data-[state=active]:rotate-0 group-data-[state=active]:scale-100 group-data-[state=active]:opacity-100 absolute inset-0 m-auto size-6 -rotate-180 scale-0 opacity-0 duration-200" />
                                </button>
                            )}
                        </div>

                        {variant !== 'minimal' && (
                            <div className="absolute inset-0 m-auto hidden size-fit lg:block">
                                <ul className="flex gap-8 text-sm">
                                    {menuItems.map((item, index) => (
                                        <li key={index}>
                                            <Link
                                                href={item.href}
                                                className="text-muted-foreground hover:text-accent-foreground block duration-150">
                                                <span>{item.name}</span>
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div className="bg-background group-data-[state=active]:block lg:group-data-[state=active]:flex mb-6 hidden w-full flex-wrap items-center justify-end space-y-8 rounded-3xl border p-6 shadow-2xl shadow-gray-900/10 md:flex-nowrap lg:m-0 lg:flex lg:w-fit lg:gap-6 lg:space-y-0 lg:border-transparent lg:bg-transparent lg:p-0 lg:shadow-none dark:shadow-none dark:lg:bg-transparent">
                            {variant !== 'dashboard' && (
                                <div className="lg:hidden">
                                    <ul className="space-y-6 text-base">
                                        {menuItems.map((item, index) => (
                                            <li key={index}>
                                                <Link
                                                    href={item.href}
                                                    className="text-muted-foreground hover:text-accent-foreground block duration-150">
                                                    <span>{item.name}</span>
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            <div className="flex w-full flex-col space-y-3 sm:flex-row sm:gap-3 sm:space-y-0 md:w-fit">
                                {isAuthenticated ? (
                                    <>
                                        {variant !== 'dashboard' && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={handleProfile}
                                                className={cn(isScrolled && 'lg:hidden')}>
                                                <span>Profile</span>
                                            </Button>
                                        )}
                                        <Button
                                            size="sm"
                                            onClick={handleLogout}
                                            className={cn(isScrolled && 'lg:hidden')}>
                                            <span>Logout</span>
                                        </Button>
                                        {variant === 'hero' ? (
                                            <Button
                                                size="sm"
                                                onClick={handleDashboard}
                                                className={cn(isScrolled ? 'lg:inline-flex' : 'hidden')}>
                                                <span>Dashboard</span>
                                            </Button>
                                        ) : (
                                            <Button
                                                size="sm"
                                                onClick={handleProfile}
                                                className="lg:inline-flex">
                                                <span>Profile</span>
                                            </Button>
                                        )}
                                    </>
                                ) : (
                                    <>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleLogin}
                                            className={cn(isScrolled && 'lg:hidden')}>
                                            <span>Login</span>
                                        </Button>
                                        <Button
                                            size="sm"
                                            onClick={handleSignup}
                                            className={cn(isScrolled && 'lg:hidden')}>
                                            <span>Sign Up</span>
                                        </Button>
                                        <Button
                                            size="sm"
                                            onClick={handleSignup}
                                            className={cn(isScrolled ? 'lg:inline-flex' : 'hidden')}>
                                            <span>Get Started</span>
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </nav>
        </header>
    )
}

export { Logo }