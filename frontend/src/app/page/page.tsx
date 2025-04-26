// src/app/page/page.tsx
"use client";

import React, { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import {
    // Bars3Icon,
    // XMarkIcon,
    DocumentTextIcon,
    LinkIcon,
    PlayCircleIcon,
    PaperAirplaneIcon,
    ArrowPathIcon,
    ChevronDoubleLeftIcon, // Icon for Collapse state button
    ChevronDoubleRightIcon, // Icon for Expand state button
} from '@heroicons/react/24/solid'; // Using solid for visual weight
import Link from 'next/link';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface Source {
    id: string;
    title: string;
    type: 'document' | 'web' | 'youtube';
    link?: string;
}

interface PageData {
    sources: Source[];
    title: string;
    summary: string;
}

const SourceIcon: React.FC<{ type: Source['type'], className?: string }> = ({ type, className = "h-5 w-5" }) => {
    switch (type) {
        case 'document':
            return <DocumentTextIcon className={className} aria-label="Document"/>;
        case 'web':
            return <LinkIcon className={className} aria-label="Web Link"/>;
        case 'youtube':
            return <PlayCircleIcon className={className} aria-label="YouTube Video"/>;
        default:
            return <DocumentTextIcon className={className} aria-label="Source"/>;
    }
};

function PageContent() {
    const searchParams = useSearchParams();
    const pageId = searchParams.get('page_id');

    // --- UI State ---
    const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Sidebar starts open

    // --- Data State ---
    const [pageData, setPageData] = useState<PageData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // --- Chat State ---
    const [chatMessages, setChatMessages] = useState<{ type: 'user' | 'bot'; text: string }[]>([]);
    const [currentInput, setCurrentInput] = useState('');
    const [isChatting, setIsChatting] = useState(false);

    // --- Fetch Data Effect ---
    useEffect(() => {
        if (!pageId) {
            setError("Page ID is missing in the URL.");
            setIsLoading(false);
            return;
        }
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            setPageData(null);
            try {
                const response = await fetch(`${BACKEND_URL}/fetch-page?page_id=${pageId}`);
                if (!response.ok) {
                    let errorDetail = `Failed to fetch page data (Status: ${response.status})`;
                    try { const errorData = await response.json(); errorDetail = errorData.detail || errorDetail; } catch { /* Ignore */ }
                    throw new Error(errorDetail);
                }
                const data: PageData = await response.json();
                if (!data || !data.title || data.summary === undefined || !Array.isArray(data.sources)) {
                     throw new Error("Received invalid data structure from server.");
                }
                setPageData(data);
            } catch (err) {
                console.error("Error fetching page data:", err);
                setError(err instanceof Error ? err.message : "An unknown error occurred while fetching page data.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [pageId]);

    // --- Handlers ---
    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setCurrentInput(event.target.value);
        event.target.style.height = 'auto';
        event.target.style.height = `${event.target.scrollHeight}px`;
    };
    const handleSend = () => {
        const query = currentInput.trim();
        if (!query || isChatting || !pageId) return;
        setChatMessages(prev => [...prev, { type: 'user', text: query }]);
        setCurrentInput('');
        const textarea = document.getElementById('chat-input-area') as HTMLTextAreaElement;
        if (textarea) textarea.style.height = 'auto';
        setIsChatting(true);
        console.log("Sending query (placeholder):", { query, pageId });
        setTimeout(() => {
            setChatMessages(prev => [...prev, { type: 'bot', text: `Placeholder response for: "${query}"` }]);
            setIsChatting(false);
        }, 1000);
    };
    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); handleSend();
        }
    };
    const handleResetChat = () => { if (chatMessages.length > 0) { setChatMessages([]); } };

    // --- Render Logic ---
    if (isLoading) return <LoadingSpinner pageId={pageId} />;
    if (error) return <ErrorDisplay error={error} />;
    if (!pageData) return <div className="flex min-h-screen items-center justify-center bg-gray-100"><p>Page data is unavailable.</p></div>;


    // --- Main Layout Render ---
    return (
        // Outer container for padding around the entire content
        <div className="h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50 p-4 md:p-5 lg:p-6">
            {/* Inner container for the actual app layout (sidebar + main) */}
            <div className="flex h-full w-full bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200/50">

                {/* --- Sidebar --- */}
                <aside
                    className={`
                        flex-shrink-0 bg-purple-50/50 border-r border-purple-100/80 transition-all duration-300 ease-in-out overflow-hidden
                        ${isSidebarOpen ? 'w-64' : 'w-16'} {/* CHANGE: Width for collapsed state */}
                    `}
                >
                    {/* Sidebar content adjusts based on open state */}
                    <div className="h-full flex flex-col">
                         {/* Header Section (Includes Toggle Button) */}
                        <div className={`flex items-center border-b border-purple-200/80 flex-shrink-0 ${isSidebarOpen ? 'justify-between p-4' : 'justify-center p-2 py-3'}`}>
                            {isSidebarOpen && (
                                <h2 className="text-lg font-semibold text-purple-800">
                                    Sources
                                </h2>
                            )}
                             <button
                                onClick={toggleSidebar}
                                className={`p-1.5 rounded-md text-purple-700 hover:bg-purple-200/70 hover:text-purple-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 focus:ring-offset-purple-50 transition-colors`}
                                aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                             >
                                {isSidebarOpen ? <ChevronDoubleLeftIcon className="h-5 w-5" /> : <ChevronDoubleRightIcon className="h-5 w-5" />}
                             </button>
                        </div>


                        {/* Sources List (Scrollable Area) */}
                        <nav className="flex-grow overflow-y-auto overflow-x-hidden" style={{ scrollbarWidth: 'thin' }}>
                           {isSidebarOpen ? (
                                // -- Expanded View --
                                <ul className="space-y-1 p-3">
                                    {pageData.sources.length > 0 ? pageData.sources.map((source) => (
                                        <li key={source.id}>
                                             {source.link ? (
                                                <Link
                                                    href={source.link} target="_blank" rel="noopener noreferrer"
                                                    className="flex items-center space-x-2.5 p-2 rounded-md text-sm text-gray-700 hover:bg-purple-100 hover:text-purple-800 group transition-colors duration-150"
                                                    title={source.title}
                                                >
                                                    <SourceIcon type={source.type} className="h-5 w-5 flex-shrink-0 text-purple-600 group-hover:text-purple-800" />
                                                    <span className="truncate flex-grow">{source.title}</span>
                                                </Link>
                                            ) : (
                                                <div className="flex items-center space-x-2.5 p-2 rounded-md text-sm text-gray-600 cursor-default group" title={source.title}>
                                                    <SourceIcon type={source.type} className="h-5 w-5 flex-shrink-0 text-gray-500" />
                                                    <span className="truncate flex-grow">{source.title}</span>
                                                </div>
                                            )}
                                        </li>
                                    )) : <li className="p-2 text-sm text-gray-500 italic">No sources.</li>}
                                </ul>
                            ) : (
                                // -- Collapsed View (Icons Only) --
                                <ul className="space-y-2 p-2 mt-2 flex flex-col items-center">
                                     {pageData.sources.map((source) => (
                                        <li key={source.id}>
                                            {source.link ? (
                                                <Link
                                                    href={source.link} target="_blank" rel="noopener noreferrer"
                                                    className="flex items-center justify-center p-2 rounded-lg text-purple-700 hover:bg-purple-200/70 hover:text-purple-900 group transition-colors duration-150"
                                                    title={source.title} // Tooltip is crucial here
                                                >
                                                    <SourceIcon type={source.type} className="h-6 w-6 flex-shrink-0" />
                                                </Link>
                                            ) : (
                                                <div className="flex items-center justify-center p-2 rounded-lg text-gray-500 cursor-default group" title={source.title}>
                                                    <SourceIcon type={source.type} className="h-6 w-6 flex-shrink-0" />
                                                </div>
                                            )}
                                        </li>
                                     ))}
                                </ul>
                           )}
                        </nav>
                    </div>
                </aside>

                {/* --- Main Content Area (Chat) --- */}
                <main className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-white to-gray-50/50">
                     {/* Top Bar (Inside Main) */}
                    <header className="flex-shrink-0 bg-white/80 backdrop-blur-sm border-b border-gray-200/80 px-4 py-3 flex items-center justify-between z-10">
                        {/* Page Title - Placed here for better alignment */}
                         <h1 className="text-xl font-semibold text-gray-800 truncate pl-2" title={pageData.title}>
                             {pageData.title}
                         </h1>

                        {/* Reset Chat Button */}
                        <button
                            onClick={handleResetChat} disabled={chatMessages.length === 0 || isChatting}
                            className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 ${
                                chatMessages.length > 0 && !isChatting ? 'text-purple-700 bg-purple-100 hover:bg-purple-200' : 'text-gray-400 bg-gray-100 cursor-not-allowed'}`}
                            aria-label="Reset Chat"
                         >
                             <ArrowPathIcon className="h-4 w-4"/>
                             <span>Reset</span> {/* Shortened label */}
                        </button>
                    </header>

                    {/* Chat Display Area */}
                    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4"> {/* Removed bg-gray-50 */}
                         {chatMessages.length === 0 ? (
                             <div className="flex flex-col items-center justify-center h-full text-center pt-4 pb-10">
                                 <h2 className="text-2xl font-semibold text-gray-800 mb-3">{pageData.title}</h2>
                                 <p className="text-gray-600 max-w-xl leading-relaxed">{pageData.summary}</p>
                                 {/* Suggestion Area Placeholder */}
                                 <div className="mt-8 text-sm text-gray-500">
                                     {/* Suggested questions can go here */}
                                 </div>
                             </div>
                         ) : (
                             chatMessages.map((msg, index) => (
                                <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl rounded-lg px-4 py-2.5 shadow-sm break-words ${
                                        msg.type === 'user' ? 'bg-purple-600 text-white' : 'bg-white text-gray-800 border border-gray-200/80'
                                    }`}>
                                        <p style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                                    </div>
                                </div>
                             ))
                         )}
                         {isChatting && (
                            <div className="flex justify-start">
                                 <div className="max-w-xs md:max-w-md rounded-lg px-4 py-2.5 shadow-sm bg-white text-gray-500 border border-gray-200/80 italic">
                                    Thinking...
                                 </div>
                            </div>
                         )}
                    </div>

                    {/* Chat Input Area */}
                    <footer className="flex-shrink-0 border-t border-gray-200/80 p-3 md:p-4 bg-white/90 backdrop-blur-sm">
                        <div className="flex items-end space-x-2">
                            <textarea
                                id="chat-input-area" rows={1} value={currentInput} onChange={handleInputChange} onKeyDown={handleKeyDown}
                                placeholder="Ask anything..."
                                className="flex-1 resize-none overflow-y-auto rounded-lg border border-gray-300/90 px-3.5 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm shadow-sm max-h-32 bg-white"
                                style={{ scrollbarWidth: 'thin' }} disabled={isChatting}
                            />
                            <button
                                onClick={handleSend} disabled={!currentInput.trim() || isChatting}
                                className={`p-2 rounded-lg text-white transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 ${
                                    !currentInput.trim() || isChatting ? 'bg-purple-300 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'}`}
                                aria-label="Send message"
                            >
                                <PaperAirplaneIcon className="h-5 w-5" />
                            </button>
                        </div>
                    </footer>
                </main>
            </div>
        </div>
    );
}


// --- Loading Spinner Component ---
const LoadingSpinner: React.FC<{ pageId: string | null }> = ({ pageId }) => (
    <div className="flex min-h-screen items-center justify-center bg-white">
        <div className="text-center p-8">
            <svg className="animate-spin h-10 w-10 text-purple-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-lg font-medium text-gray-700">Loading Page...</p>
            {pageId && <p className="text-sm text-gray-500 mt-1">ID: {pageId}</p>}
        </div>
    </div>
);

// --- Error Display Component ---
const ErrorDisplay: React.FC<{ error: string }> = ({ error }) => (
    <div className="flex min-h-screen items-center justify-center bg-red-50 p-4">
        <div className="text-center p-8 bg-white rounded-lg shadow-md max-w-md w-full">
            <h1 className="text-2xl font-semibold text-red-600 mb-4">Error</h1>
            <p className="text-gray-700 mb-6">{error}</p>
            <Link href="/" className="inline-block px-5 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 transition-colors shadow-sm">
                Go to Home
            </Link>
        </div>
    </div>
);


// --- Main Export with Suspense ---
export default function Page() {
    return (
        <Suspense fallback={ // Fallback can be simpler now, LoadingSpinner handles detailed loading
             <div className="flex min-h-screen items-center justify-center bg-white">
                 <p className="text-lg font-medium text-gray-700">Loading...</p>
             </div>
        }>
            <PageContent />
        </Suspense>
    );
}