"use client";

import { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

export default function Login() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Demo credentials
    const DEMO_EMAIL = 'demo@example.com';
    const DEMO_PASSWORD = 'password123';

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Simple validation
        if (!email || !password) {
            setError('Please enter both email and password');
            setLoading(false);
            return;
        }

        // Check if using demo credentials or allow any credentials for now
        if ((email === DEMO_EMAIL && password === DEMO_PASSWORD) || true) {
            // Store authentication state
            localStorage.setItem('isLoggedIn', 'true');

            // Redirect to main page
            setTimeout(() => {
                router.push('/');
            }, 500);
        } else {
            setError('Invalid credentials');
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen">
            <div className="flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
                <div className="mx-auto w-full max-w-sm lg:w-96">
                    <div>

                        <h2 className="mt-8 text-2xl font-bold leading-9 tracking-tight text-gray-900">
                            Sign in to News Search
                        </h2>
                        <p className="mt-2 text-sm leading-6 text-gray-500">
                            Use demo credentials:
                            <span className="font-mono text-indigo-600 ml-1">
                                {DEMO_EMAIL} / {DEMO_PASSWORD}
                            </span>
                        </p>
                    </div>

                    <div className="mt-10">
                        {error && (
                            <div className="mb-4 p-2 bg-red-50 text-red-700 text-sm rounded border border-red-200">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900">
                                    Email address
                                </label>
                                <div className="mt-2">
                                    <input
                                        id="email"
                                        name="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        autoComplete="email"
                                        placeholder={DEMO_EMAIL}
                                        className="block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900">
                                    Password
                                </label>
                                <div className="mt-2">
                                    <input
                                        id="password"
                                        name="password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        autoComplete="current-password"
                                        placeholder="••••••••"
                                        className="block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                    />
                                </div>
                            </div>

                            <div>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-70"
                                >
                                    {loading ? 'Signing in...' : 'Sign in'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            <div className="relative hidden w-0 flex-1 lg:block">
                <Image
                    alt=""
                    src="https://images.unsplash.com/photo-1496917756835-20cb06e75b4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1908&q=80"
                    layout="fill"
                    objectFit="cover"
                    className="absolute inset-0 h-full w-full"
                />
            </div>
        </div>
    );
}