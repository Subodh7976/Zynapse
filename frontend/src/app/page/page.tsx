// src/app/page/page.tsx
"use client"; // Needed for useSearchParams

import React, { Suspense } from 'react'; // Import Suspense
import { useSearchParams } from 'next/navigation';

// A simple component to read search params
function PageContent() {
    const searchParams = useSearchParams();
    const pageId = searchParams.get('page_id');

    if (!pageId) {
        return (
             <div className="flex min-h-screen items-center justify-center bg-gray-100">
                <div className="text-center p-8">
                    <h1 className="text-2xl font-semibold text-red-600 mb-4">Error</h1>
                    <p className="text-gray-700">Page ID is missing.</p>
                    {/* Optionally add a link back home */}
                    {/* <a href="/" className="text-purple-600 hover:underline mt-4 inline-block">Go back home</a> */}
                </div>
            </div>
        );
    }

    // Placeholder for the actual page content (Sidebar, Chat Interface etc.)
    return (
        <div className="flex min-h-screen items-center justify-center bg-white">
            <div className="text-center p-8">
                <h1 className="text-3xl font-bold text-purple-700 mb-4">Page Loading...</h1>
                <p className="text-gray-600">Page ID: <span className="font-mono bg-gray-100 px-1 rounded">{pageId}</span></p>
                <p className="text-gray-500 mt-4">Content will be loaded here.</p>
                {/* We will replace this with the actual layout */}
            </div>
        </div>
    );
}


// The main export uses Suspense to wrap the component that uses useSearchParams
export default function Page() {
    return (
        <Suspense fallback={ // Fallback UI while Suspense boundary is resolving
             <div className="flex min-h-screen items-center justify-center bg-white">
                 <div className="text-center p-8">
                     <h1 className="text-3xl font-bold text-purple-700 mb-4">Loading Page...</h1>
                     {/* You can add a spinner here */}
                 </div>
             </div>
        }>
            <PageContent />
        </Suspense>
    );
}