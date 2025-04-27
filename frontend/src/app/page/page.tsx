"use client";

import React, {
  Suspense,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { useSearchParams } from "next/navigation";
import {
  DocumentTextIcon,
  LinkIcon,
  PlayCircleIcon,
  PaperAirplaneIcon,
  ArrowPathIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  ClockIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/solid";
import Link from "next/link";
import { useTypewriter } from "@/hooks/useTypewriter";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://34.55.180.24:8000";

interface Source {
  id: string;
  title: string;
  type: "document" | "web" | "youtube";
  link?: string;
}

interface PageData {
  sources: Source[];
  title: string;
  summary: string;
}

interface Update {
  type: "status" | "sources" | "message" | "error";
  content: string | string[];
}

interface PollingResponse {
  type: Update["type"];
  content: Update["content"];
  updates: Update[];
}

interface ChatMessage {
  id: string;
  type: "user" | "bot";
  text: string;
  status?: string | null;
  statusHistory?: string[];
  isStreaming?: boolean;
  isFinished?: boolean;
  error?: string | null;
}

const SourceIcon: React.FC<{ type: Source["type"]; className?: string }> = ({
  type,
  className = "h-5 w-5",
}) => {
  switch (type) {
    case "document":
      return <DocumentTextIcon className={className} aria-label="Document" />;
    case "web":
      return <LinkIcon className={className} aria-label="Web Link" />;
    case "youtube":
      return (
        <PlayCircleIcon className={className} aria-label="YouTube Video" />
      );
    default:
      return <DocumentTextIcon className={className} aria-label="Source" />;
  }
};

function PageContent() {
  // --- UI State ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // --- Data State ---
  const [pageData, setPageData] = useState<PageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- Chat State ---
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [openStatusHistoryId, setOpenStatusHistoryId] = useState<string | null>(
    null
  );

  // --- Polling State ---
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateTimeRef = useRef<number | null>(null);
  const lastResponseSignatureRef = useRef<string | null>(null);
  const processedUpdateIndicesRef = useRef<Record<string, number>>({});

  const searchParams = useSearchParams();
  const pageId = searchParams.get("page_id");

  const stopPolling = useCallback(() => {
    const requestIdToStop = currentRequestId;

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      console.log(
        "Polling interval cleared by stopPolling for request:",
        requestIdToStop
      );
    } else {
      console.log(
        "stopPolling called, but no active interval found for request:",
        requestIdToStop
      );
    }

    // Reset refs
    lastUpdateTimeRef.current = null;
    lastResponseSignatureRef.current = null;

    if (requestIdToStop) {
      setChatMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === requestIdToStop && msg.type === "bot"
            ? { ...msg, isStreaming: false, status: null, isFinished: true }
            : msg
        )
      );
    }

    setCurrentRequestId(null);
    setIsChatting(false);

    console.log("Polling stopped for request:", requestIdToStop);
  }, [currentRequestId]);

  const pollForUpdates = useCallback(
    async (requestId: string) => {
      if (!requestId || requestId !== currentRequestId) {
        // Safety check
        console.warn(
          "Polling attempted with invalid or mismatched requestId. Stopping."
        );
        return;
      }

      console.log("Polling for request:", requestId); // Debug log

      try {
        const response = await fetch(
          `${BACKEND_URL}/chat?request_id=${requestId}`
        );

        if (!response.ok) {
          let errorDetail = `Polling failed with status ${response.status}`;
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail;
          } catch {
            /* Ignore if error response isn't JSON */
          }
          throw new Error(errorDetail);
        }

        const data: PollingResponse = await response.json();
        console.log("Poll response:", data); // Debug log

        const currentSignature = JSON.stringify({
          type: data.type,
          content: data.content,
        });

        // --- Timeout Check ---
        if (lastResponseSignatureRef.current === currentSignature) {
          if (
            lastUpdateTimeRef.current &&
            Date.now() - lastUpdateTimeRef.current > 60000
          ) {
            console.log("Polling timeout reached for request:", requestId);
            setChatMessages((prev) =>
              prev.map((msg) =>
                msg.id === requestId
                  ? {
                      ...msg,
                      error: "Response timed out.",
                      status: "Timeout",
                      isStreaming: false,
                      isFinished: true,
                    }
                  : msg
              )
            );
            stopPolling();
            return;
          }
        } else {
          lastResponseSignatureRef.current = currentSignature;
          lastUpdateTimeRef.current = Date.now();
        }

        // --- Process Updates Array ---
        let shouldStopPolling = false;
        let latestMessageContent = "";

        const lastProcessedIndex =
          processedUpdateIndicesRef.current[requestId] ?? -1;

        for (let i = lastProcessedIndex + 1; i < data.updates.length; i++) {
          const update = data.updates[i];
          if (
            (update.type === "status" && update.content === "finished") ||
            update.type === "error"
          ) {
            shouldStopPolling = true;
            break;
          }
        }

        if (!shouldStopPolling) {
          if (
            (data.type === "status" && data.content === "finished") ||
            data.type === "error"
          ) {
            shouldStopPolling = true;
          }
        }

        // First pass: Process the `updates` array to update history and latestMessageContent
        setChatMessages((prevMessages) =>
          prevMessages.map((msg) => {
            if (msg.id === requestId && msg.type === "bot") {
              const workingMsg = { ...msg };
              workingMsg.statusHistory = workingMsg.statusHistory
                ? [...workingMsg.statusHistory]
                : [];

              const currentLastProcessed =
                processedUpdateIndicesRef.current[requestId] ?? -1;
              let newLastProcessed = currentLastProcessed;

              for (let i = 0; i < data.updates.length; i++) {
                const update = data.updates[i];
                if (i <= currentLastProcessed) continue;

                let statusContentToAdd: string | null = null;

                switch (update.type) {
                  case "status":
                    statusContentToAdd = update.content as string;
                    break;
                  case "sources":
                    if (
                      Array.isArray(update.content) &&
                      update.content.length > 0
                    ) {
                      const sourceNames = update.content.join(", ");
                      statusContentToAdd = `Reading source: ${sourceNames}`;
                    } else {
                      statusContentToAdd = "Processing sources...";
                    }
                    break;
                  case "message":
                    latestMessageContent = update.content as string;
                    break;
                  case "error":
                    statusContentToAdd = `Error: ${update.content as string}`;
                    break;
                }

                if (
                  statusContentToAdd &&
                  workingMsg.statusHistory[
                    workingMsg.statusHistory.length - 1
                  ] !== statusContentToAdd
                ) {
                  workingMsg.statusHistory.push(statusContentToAdd);
                }
                newLastProcessed = i;
              }
              processedUpdateIndicesRef.current[requestId] = newLastProcessed;

              if (latestMessageContent) {
                workingMsg.text = latestMessageContent;
              }

              return workingMsg;
            }
            return msg;
          })
        );

        // Second pass: Apply the *latest* root status/error/streaming state from `data`
        // This ensures the final visible state matches the absolute latest info from the backend.
        setChatMessages((prevMessages) =>
          prevMessages.map((msg) => {
            if (msg.id === requestId && msg.type === "bot") {
              let finalStatus = msg.status;
              let finalError = msg.error;
              let finalIsStreaming = msg.isStreaming;
              let finalIsFinished = msg.isFinished;

              if (data.type === "message") {
                finalStatus = null;
                finalIsStreaming = true;
              } else if (data.type === "status") {
                finalStatus = data.content as string;
                finalIsStreaming = data.content !== "finished";
              } else if (data.type === "error") {
                finalError = data.content as string;
                finalStatus = "Error occurred";
                finalIsStreaming = false;
              }

              if (shouldStopPolling) {
                finalIsStreaming = false;
                finalIsFinished = true;
                finalStatus = finalStatus === "finished" ? null : finalStatus;
              }

              return {
                ...msg,
                status: finalStatus,
                error: finalError,
                isStreaming: finalIsStreaming,
                isFinished: finalIsFinished,
              };
            }
            return msg;
          })
        );

        // --- Final Check for Stop Conditions ---
        if (shouldStopPolling) {
          console.log("Stop condition met in poll response for:", requestId);
          stopPolling();
        }
      } catch (error) {
        console.error("Error during polling:", error);
        const errorMsg = error instanceof Error ? error.message : String(error);
        setChatMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === requestId && msg.type === "bot"
              ? {
                  ...msg,
                  isStreaming: false,
                  status: "Polling Error",
                  error: errorMsg,
                  isFinished: true,
                }
              : msg
          )
        );
        stopPolling();
      }
    },
    [currentRequestId, stopPolling]
  );

  const startPolling = useCallback(
    (requestId: string) => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      processedUpdateIndicesRef.current[requestId] = -1;
      lastResponseSignatureRef.current = null;
      lastUpdateTimeRef.current = Date.now();

      // Start interval
      pollingIntervalRef.current = setInterval(() => {
        pollForUpdates(requestId);
      }, 300);
    },
    [pollForUpdates]
  );

  // --- Cleanup Effect ---
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        console.log("Polling interval cleared on component unmount.");
      }
    };
  }, []);

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
        const response = await fetch(
          `${BACKEND_URL}/fetch-page?page_id=${pageId}`
        );
        if (!response.ok) {
          let errorDetail = `Failed to fetch page data (Status: ${response.status})`;
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail;
          } catch {
            /* Ignore */
          }
          throw new Error(errorDetail);
        }
        const data: PageData = await response.json();
        if (
          !data ||
          !data.title ||
          data.summary === undefined ||
          !Array.isArray(data.sources)
        ) {
          throw new Error("Received invalid data structure from server.");
        }
        setPageData(data);
      } catch (err) {
        console.error("Error fetching page data:", err);
        setError(
          err instanceof Error
            ? err.message
            : "An unknown error occurred while fetching page data."
        );
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [pageId]);

  useEffect(() => {
    if (currentRequestId) {
      console.log(
        "useEffect triggered: Starting polling for",
        currentRequestId
      );
      startPolling(currentRequestId);
    } else {
      console.log("useEffect triggered: Ensuring polling is stopped.");
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    return () => {
      console.log(
        "useEffect cleanup: Clearing interval for request (if any):",
        currentRequestId
      );
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [currentRequestId, startPolling]);

  // --- Handlers ---
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCurrentInput(event.target.value);
    event.target.style.height = "auto";
    event.target.style.height = `${event.target.scrollHeight}px`;
  };

  const handleSend = useCallback(async () => {
    const query = currentInput.trim();
    if (!query || isChatting || !pageId) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: "user",
      text: query,
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setCurrentInput("");
    setIsChatting(true);

    // Reset textarea height
    const textarea = document.getElementById(
      "chat-input-area"
    ) as HTMLTextAreaElement;
    if (textarea) textarea.style.height = "auto";

    let tempRequestId: string | null = null;

    try {
      console.log("Initiating chat with query:", query, "pageId:", pageId);
      const initResponse = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ query: query, page_id: pageId }),
      });

      if (!initResponse.ok) {
        let errorDetail = `Failed to initiate chat (Status: ${initResponse.status})`;
        try {
          const errorData = await initResponse.json();
          errorDetail = errorData.detail || errorDetail;
        } catch {
          /* Ignore */
        }
        throw new Error(errorDetail);
      }

      const initData = await initResponse.json();
      tempRequestId = initData.request_id;
      const receivedRequestId = initData.request_id;

      if (!tempRequestId) {
        throw new Error("No request_id received from the server.");
      }

      const botPlaceholder: ChatMessage = {
        id: receivedRequestId,
        type: "bot",
        text: "",
        status: "Initializing...",
        isStreaming: true,
        isFinished: false,
      };
      setChatMessages((prev) => [...prev, botPlaceholder]);

      setCurrentRequestId(receivedRequestId);
    } catch (error) {
      console.error("Error initiating chat or starting poll:", error);
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        type: "bot",
        text: `Error: ${
          error instanceof Error ? error.message : "Could not start chat."
        }`,
        isStreaming: false,
        isFinished: true,
        error: error instanceof Error ? error.message : String(error),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
      setIsChatting(false);
      setCurrentRequestId(null);
    }
  }, [currentInput, isChatting, pageId]);
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };
  const handleResetChat = useCallback(() => {
    if (chatMessages.length > 0) {
      stopPolling();
      setChatMessages([]);
      processedUpdateIndicesRef.current = {};
    }
  }, [chatMessages.length, stopPolling]);

  // --- Render Logic ---
  if (isLoading) return <LoadingSpinner pageId={pageId} />;
  if (error) return <ErrorDisplay error={error} />;
  if (!pageData)
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <p>Page data is unavailable.</p>
      </div>
    );

  // --- Main Layout Render ---
  return (
    <div className="h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50 p-4 md:p-5 lg:p-6">
      {/* Inner container for the actual app layout (sidebar + main) */}
      <div className="flex h-full w-full bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200/50">
        {/* --- Sidebar --- */}
        <aside
          className={`
                        flex-shrink-0 bg-purple-50/50 border-r border-purple-100/80 transition-all duration-300 ease-in-out overflow-hidden
                        ${
                          isSidebarOpen ? "w-64" : "w-16"
                        } {/* CHANGE: Width for collapsed state */}
                    `}
        >
          {/* Sidebar content adjusts based on open state */}
          <div className="h-full flex flex-col">
            {/* Header Section (Includes Toggle Button) */}
            <div
              className={`flex items-center border-b border-purple-200/80 flex-shrink-0 ${
                isSidebarOpen
                  ? "justify-between p-4"
                  : "justify-center p-2 py-3"
              }`}
            >
              {isSidebarOpen && (
                <h2 className="text-lg font-semibold text-purple-800">
                  Sources
                </h2>
              )}
              <button
                onClick={toggleSidebar}
                className={`p-1.5 rounded-md text-purple-700 hover:bg-purple-200/70 hover:text-purple-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 focus:ring-offset-purple-50 transition-colors`}
                aria-label={
                  isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"
                }
              >
                {isSidebarOpen ? (
                  <ChevronDoubleLeftIcon className="h-5 w-5" />
                ) : (
                  <ChevronDoubleRightIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            {/* Sources List (Scrollable Area) */}
            <nav
              className="flex-grow overflow-y-auto overflow-x-hidden"
              style={{ scrollbarWidth: "thin" }}
            >
              {isSidebarOpen ? (
                // -- Expanded View --
                <ul className="space-y-1 p-3">
                  {pageData.sources.length > 0 ? (
                    pageData.sources.map((source) => (
                      <li key={source.id}>
                        {source.link ? (
                          <Link
                            href={source.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-2.5 p-2 rounded-md text-sm text-gray-700 hover:bg-purple-100 hover:text-purple-800 group transition-colors duration-150"
                            title={source.title}
                          >
                            <SourceIcon
                              type={source.type}
                              className="h-5 w-5 flex-shrink-0 text-purple-600 group-hover:text-purple-800"
                            />
                            <span className="truncate flex-grow">
                              {source.title}
                            </span>
                          </Link>
                        ) : (
                          <div
                            className="flex items-center space-x-2.5 p-2 rounded-md text-sm text-gray-600 cursor-default group"
                            title={source.title}
                          >
                            <SourceIcon
                              type={source.type}
                              className="h-5 w-5 flex-shrink-0 text-gray-500"
                            />
                            <span className="truncate flex-grow">
                              {source.title}
                            </span>
                          </div>
                        )}
                      </li>
                    ))
                  ) : (
                    <li className="p-2 text-sm text-gray-500 italic">
                      No sources.
                    </li>
                  )}
                </ul>
              ) : (
                // -- Collapsed View (Icons Only) --
                <ul className="space-y-2 p-2 mt-2 flex flex-col items-center">
                  {pageData.sources.map((source) => (
                    <li key={source.id}>
                      {source.link ? (
                        <Link
                          href={source.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-center p-2 rounded-lg text-purple-700 hover:bg-purple-200/70 hover:text-purple-900 group transition-colors duration-150"
                          title={source.title} // Tooltip is crucial here
                        >
                          <SourceIcon
                            type={source.type}
                            className="h-6 w-6 flex-shrink-0"
                          />
                        </Link>
                      ) : (
                        <div
                          className="flex items-center justify-center p-2 rounded-lg text-gray-500 cursor-default group"
                          title={source.title}
                        >
                          <SourceIcon
                            type={source.type}
                            className="h-6 w-6 flex-shrink-0"
                          />
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
            <h1
              className="text-xl font-semibold text-gray-800 truncate pl-2"
              title={pageData.title}
            >
              {pageData.title}
            </h1>

            {/* Reset Chat Button */}
            <button
              onClick={handleResetChat}
              disabled={chatMessages.length === 0 || isChatting}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 ${
                chatMessages.length > 0 && !isChatting
                  ? "text-purple-700 bg-purple-100 hover:bg-purple-200"
                  : "text-gray-400 bg-gray-100 cursor-not-allowed"
              }`}
              aria-label="Reset Chat"
            >
              <ArrowPathIcon className="h-4 w-4" />
              <span>Reset</span> {/* Shortened label */}
            </button>
          </header>
          {/* Chat Display Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
            {chatMessages.length === 0 && pageData ? (
              <div className="flex flex-col items-center justify-center h-full text-center pt-4 pb-10">
                <h2 className="text-2xl font-semibold text-gray-800 mb-3">
                  {pageData.title}
                </h2>
                <p className="text-gray-600 max-w-xl leading-relaxed">
                  {pageData.summary}
                </p>
                {/* Suggestion Area Placeholder */}
              </div>
            ) : (
              chatMessages.map((msg) => (
                <ChatMessageItem
                  key={msg.id}
                  message={msg}
                  openStatusHistoryId={openStatusHistoryId}
                  setOpenStatusHistoryId={setOpenStatusHistoryId}
                />
              ))
            )}
          </div>
          {/* Chat Input Area */}
          <footer className="flex-shrink-0 border-t border-gray-200/80 p-3 md:p-4 bg-white/90 backdrop-blur-sm">
            <div className="flex items-end space-x-2">
              <textarea
                id="chat-input-area"
                rows={1}
                value={currentInput}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything..."
                className="flex-1 resize-none overflow-y-auto rounded-lg border border-gray-300/90 px-3.5 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm shadow-sm max-h-32 bg-white"
                style={{ scrollbarWidth: "thin" }}
                disabled={isChatting}
              />
              <button
                onClick={handleSend}
                disabled={!currentInput.trim() || isChatting}
                className={`p-2 rounded-lg text-white transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1 ${
                  !currentInput.trim() || isChatting
                    ? "bg-purple-300 cursor-not-allowed"
                    : "bg-purple-600 hover:bg-purple-700"
                }`}
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
      <svg
        className="animate-spin h-10 w-10 text-purple-600 mx-auto mb-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        ></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
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
      <Link
        href="/"
        className="inline-block px-5 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 transition-colors shadow-sm"
      >
        Go to Home
      </Link>
    </div>
  </div>
);

interface ChatMessageItemProps {
  message: ChatMessage;
  openStatusHistoryId: string | null;
  setOpenStatusHistoryId: (id: string | null) => void;
}

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message: msg,
  openStatusHistoryId,
  setOpenStatusHistoryId,
}) => {
  const displayedText = useTypewriter(
    msg.text || "",
    msg.type === "bot" && (msg.isStreaming ?? false)
  );

  useEffect(() => {
    if (msg.type === "bot" && msg.isStreaming) {
      const scrollArea = document.getElementById("chat-scroll-area");
      if (scrollArea) {
        requestAnimationFrame(() => {
          scrollArea.scrollTop = scrollArea.scrollHeight;
        });
      }
    }
  }, [displayedText, msg.type, msg.isStreaming]);

  return (
    <div
      className={`flex ${
        msg.type === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {/* Container for bubble + status/history */}
      <div
        className={`flex flex-col max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl ${
          msg.type === "user" ? "items-end" : "items-start"
        }`}
      >
        {/* --- Status Indicator OR History Toggle (Appears ABOVE bubble for bot) --- */}
        {msg.type === "bot" && (
          <>
            {/* Live Status */}
            {msg.isStreaming && !msg.isFinished && msg.status && !msg.error && (
              <div className="flex items-center space-x-1.5 mb-1.5 px-2 py-0.5 text-xs text-gray-500 italic bg-gray-100 rounded-full">
                {/* Spinner */}
                <svg
                  className="animate-spin h-3 w-3 text-gray-500"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>{msg.status}</span>
              </div>
            )}
            {/* Error during streaming */}
            {msg.isStreaming &&
              !msg.isFinished &&
              msg.error &&
              msg.status === "Error occurred" && (
                <div className="mb-1.5 px-2 text-xs text-red-600 italic">
                  <span>Error: {msg.error}</span>
                </div>
              )}

            {/* History Toggle Button */}
            {msg.isFinished &&
              msg.statusHistory &&
              msg.statusHistory.length > 0 && (
                <button
                  onClick={() =>
                    setOpenStatusHistoryId(
                      openStatusHistoryId === msg.id ? null : msg.id
                    )
                  }
                  className="flex items-center space-x-1 mb-1.5 px-2 py-0.5 text-xs text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-full transition-colors focus:outline-none focus:ring-1 focus:ring-purple-400"
                  aria-expanded={openStatusHistoryId === msg.id}
                  aria-controls={`status-history-${msg.id}`}
                >
                  {/* Icons */}
                  <ClockIcon className="h-3.5 w-3.5" />
                  <span>Status History</span>
                  {openStatusHistoryId === msg.id ? (
                    <ChevronUpIcon className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronDownIcon className="h-3.5 w-3.5" />
                  )}
                </button>
              )}
          </>
        )}

        {/* --- Status History List --- */}
        {msg.type === "bot" &&
          openStatusHistoryId === msg.id &&
          msg.statusHistory &&
          msg.statusHistory.length > 0 && (
            <div
              id={`status-history-${msg.id}`}
              className="mb-1.5 p-2 border border-purple-200 bg-purple-50/50 rounded-md shadow-inner w-full" // Use mb-1.5 to space it from bubble
            >
              <ul className="space-y-1 list-disc list-inside">
                {msg.statusHistory.map((status, index) => (
                  <li key={index} className="text-xs text-gray-600 italic">
                    {status}
                  </li>
                ))}
              </ul>
            </div>
          )}

        {/* Message Bubble */}
        <div
          className={`rounded-lg px-4 py-2.5 shadow-sm break-words w-fit ${
            msg.type === "user"
              ? "bg-purple-600 text-white" /* ... error/normal styling ... */
              : msg.error
              ? "bg-red-100 text-red-800 border border-red-200"
              : "bg-white text-gray-800 border border-gray-200/80"
          }`}
        >
          {/* Render the text from the useTypewriter hook */}
          <p style={{ whiteSpace: "pre-wrap" }}>
            {displayedText}
            {/* Add a blinking cursor effect while streaming */}
            {msg.type === "bot" && msg.isStreaming && !msg.isFinished && (
              <span className="inline-block w-2 h-4 ml-1 bg-gray-700 animate-pulse"></span>
            )}
          </p>
          {/* Display error directly in the bubble if needed */}
          {msg.error && !msg.status && (
            <p className="mt-1 text-xs font-medium">Error: {msg.error}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white">
          <p className="text-lg font-medium text-gray-700">Loading...</p>
        </div>
      }
    >
      <PageContent />
    </Suspense>
  );
}
