"use client";

import React, {
  useState,
  useRef,
  ChangeEvent,
  MouseEvent,
  useEffect,
} from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { useRouter } from "next/navigation";

interface CreatePageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://34.55.180.24:8000";

const CreatePageModal: React.FC<CreatePageModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [title, setTitle] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [webLinks, setWebLinks] = useState("");
  const [youtubeLinks, setYoutubeLinks] = useState("");
  const [selectedFileNames, setSelectedFileNames] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({
    current: 0,
    total: 0,
  });
  const [uploadErrors, setUploadErrors] = useState<
    { name: string; message: string }[]
  >([]);
  const [pageId, setPageId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!isOpen) {
      setTitle("");
      setFiles(null);
      setSelectedFileNames([]);
      setWebLinks("");
      setYoutubeLinks("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setIsSubmitting(false);
      setUploadProgress({ current: 0, total: 0 });
      setUploadErrors([]);
      setPageId(null);
    }
  }, [isOpen]);

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const currentFiles = event.target.files;
    setFiles(currentFiles);
    if (currentFiles) {
      const names = Array.from(currentFiles).map((file) => file.name);
      setSelectedFileNames(names);
    } else {
      setSelectedFileNames([]);
    }
  };

  const handleUploadButtonClick = () => {
    fileInputRef.current?.click();
  };

  const addUploadError = (name: string, message: string) => {
    setUploadErrors((prev) => {
      if (prev.some((err) => err.name === name && err.message === message)) {
        return prev;
      }
      return [...prev, { name, message }];
    });
  };

  const handleCreateClick = async () => {
    if (!title.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setUploadErrors([]);
    setUploadProgress({ current: 0, total: 0 });
    setPageId(null);

    let receivedPageId: string | null = null;

    try {
      // --- 1. Initiate Page Creation ---
      console.log("Initiating page creation with title:", title);
      const initResponse = await fetch(`${BACKEND_URL}/initiate-page`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      });

      if (!initResponse.ok) {
        const errorData = await initResponse.json().catch(() => ({}));
        throw new Error(
          errorData.detail ||
            `Failed to initiate page (Status: ${initResponse.status})`
        );
      }

      const initData = await initResponse.json();
      receivedPageId = initData.page_id;
      if (!receivedPageId) throw new Error("No page_id received.");
      setPageId(receivedPageId);
      console.log("Received page_id:", receivedPageId);

      // --- 2. Prepare Sources ---
      const sourcesToUpload: {
        type: "document" | "web" | "youtube";
        data: File | string;
        name: string;
      }[] = [];
      if (files) {
        Array.from(files).forEach((file) =>
          sourcesToUpload.push({
            type: "document",
            data: file,
            name: file.name,
          })
        );
      }
      webLinks
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .forEach((link) =>
          sourcesToUpload.push({ type: "web", data: link, name: link })
        );
      youtubeLinks
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .forEach((link) =>
          sourcesToUpload.push({ type: "youtube", data: link, name: link })
        );

      const totalSources = sourcesToUpload.length;
      setUploadProgress({ current: 0, total: totalSources });

      // --- 3. Upload Sources ---
      if (totalSources > 0) {
        console.log(`Starting upload of ${totalSources} sources...`);
        for (let i = 0; i < totalSources; i++) {
          const source = sourcesToUpload[i];
          const sourceName = source.name;

          setUploadProgress((prev) => ({ ...prev, current: i + 1 }));

          const formData = new FormData();
          formData.append("page_id", receivedPageId);
          formData.append("source_type", source.type);

          if (source.type === "document" && source.data instanceof File) {
            formData.append("source", source.data, source.data.name);
            console.log(
              `Appending file to FormData with key 'source': ${source.data.name}`
            );
          } else if (source.type === "web" || source.type === "youtube") {
            formData.append("url", source.data as string);
            console.log(
              `Appending URL to FormData with key 'url': ${source.data}`
            );
          } else {
            console.warn(
              `Unexpected source type '${source.type}' for source '${sourceName}'. Appending data with key 'source'.`
            );
            formData.append("source", source.data as string);
          }

          console.log(
            `Uploading source ${i + 1}/${totalSources}: ${sourceName} (${
              source.type
            })`
          );

          try {
            const uploadResponse = await fetch(`${BACKEND_URL}/upload-source`, {
              method: "POST",
              body: formData,
            });

            if (uploadResponse.ok) {
              let successData;
              try {
                successData = await uploadResponse.json();
              } catch (jsonError) {
                console.error(
                  `Error parsing JSON response for ${sourceName}:`,
                  jsonError
                );
                addUploadError(
                  sourceName,
                  `Upload OK, but failed to parse response.`
                );
                continue;
              }

              if (successData && successData.source_id) {
                console.log(
                  `Successfully uploaded ${sourceName}, received source_id: ${successData.source_id}`
                );
              } else {
                console.warn(
                  `Upload OK for ${sourceName}, but response missing 'source_id'. Treating as partial failure.`
                );
                addUploadError(
                  sourceName,
                  `Upload OK, but confirmation (source_id) missing.`
                );
              }
            } else {
              let errorDetail = `Failed with status ${uploadResponse.status}`;
              try {
                const errorData = await uploadResponse.json();
                errorDetail = errorData.detail || errorDetail;
              } catch (jsonError) {
                console.warn(
                  `Could not parse error response for ${sourceName}. Status: ${uploadResponse.status} Error ${jsonError}`
                );
              }
              console.error(`Error uploading ${sourceName}:`, errorDetail);
              addUploadError(
                sourceName,
                `Failed to add source - ${errorDetail}`
              );
            }
          } catch (uploadError) {
            console.error(
              `Network or fetch error uploading ${sourceName}:`,
              uploadError
            );
            const message =
              uploadError instanceof Error
                ? uploadError.message
                : "Network error";
            addUploadError(sourceName, `Failed to add source - ${message}`);
          }
        }
      } else {
        console.log("No sources to upload.");
      }

      // --- 4. Redirect ---
      console.log("Source processing loop finished. Redirecting...");
      router.push(`/page?page_id=${receivedPageId}`);
    } catch (error) {
      console.error("Critical error during page creation or setup:", error);
      const message =
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.";
      addUploadError("Page Initialization", message);
      setIsSubmitting(false);
    }
  };

  const handleModalContentClick = (e: MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
  };

  if (!isOpen) return null;

  const progressPercentage =
    uploadProgress.total > 0
      ? Math.round((uploadProgress.current / uploadProgress.total) * 100)
      : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 p-4 transition-opacity duration-300 ease-in-out"
      onClick={handleClose}
    >
      <div
        className="relative w-full max-w-4xl rounded-xl bg-white p-8 shadow-2xl transition-transform duration-300 ease-in-out transform scale-100"
        onClick={handleModalContentClick}
      >
        {!isSubmitting && (
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 rounded-full p-1 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
            aria-label="Close modal"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        )}

        <h2 className="mb-6 text-center text-2xl font-semibold text-gray-800">
          Create New Page
        </h2>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-6">
          <fieldset disabled={isSubmitting} className="space-y-6">
            {/* Title Input */}
            <div>
              <label
                htmlFor="pageTitle"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Page Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="pageTitle"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter a title for your page"
                required
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm py-2 px-3 disabled:cursor-not-allowed disabled:bg-gray-100"
              />
            </div>
            {/* Document Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Upload Documents (PDF only)
              </label>
              <div
                className={`mt-1 flex flex-col items-center rounded-md border-2 border-dashed border-gray-300 px-6 pt-6 pb-8 ${
                  isSubmitting ? "bg-gray-50" : ""
                }`}
              >
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  accept=".pdf"
                  multiple
                  onChange={handleFileChange}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  onClick={handleUploadButtonClick}
                  disabled={isSubmitting}
                  className="mb-2 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-500"
                >
                  Select Files
                </button>
                <p className="text-xs text-gray-500">
                  Drag and drop or select PDF files
                </p>
                {selectedFileNames.length > 0 && !isSubmitting && (
                  <div className="mt-4 text-sm text-gray-600 w-full text-left">
                    <p className="font-medium">Selected:</p>
                    <ul className="list-disc list-inside max-h-24 overflow-y-auto">
                      {selectedFileNames.map((name, index) => (
                        <li key={index} className="truncate">
                          {name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            {/* Web Links Input */}
            <div>
              <label
                htmlFor="webLinks"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Web Links (one per line)
              </label>
              <textarea
                id="webLinks"
                rows={3}
                value={webLinks}
                onChange={(e) => setWebLinks(e.target.value)}
                placeholder="https://example.com/article1
https://anothersite.org/page"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm py-2 px-3 disabled:cursor-not-allowed disabled:bg-gray-100"
                disabled={isSubmitting}
              />
            </div>
            {/* YouTube Links Input */}
            <div>
              <label
                htmlFor="youtubeLinks"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                YouTube Links (one per line)
              </label>
              <textarea
                id="youtubeLinks"
                rows={3}
                value={youtubeLinks}
                onChange={(e) => setYoutubeLinks(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=...
https://youtu.be/..."
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm py-2 px-3 disabled:cursor-not-allowed disabled:bg-gray-100"
                disabled={isSubmitting}
              />
            </div>
          </fieldset>

          {/* Progress Bar */}
          {isSubmitting && (
            <div className="space-y-2 pt-2">
              <div className="text-sm font-medium text-gray-700">
                {pageId
                  ? `Processing sources (${uploadProgress.current}/${uploadProgress.total})...`
                  : "Initiating page..."}
                {uploadErrors.length > 0 && (
                  <span className="text-red-600 ml-2">
                    ({uploadErrors.length} error
                    {uploadErrors.length > 1 ? "s" : ""})
                  </span>
                )}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all duration-300 ease-out ${
                    uploadErrors.length > 0 ? "bg-orange-500" : "bg-purple-600"
                  }`}
                  style={{ width: `${progressPercentage}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {uploadErrors.length > 0 && (
            <div className="mt-4 space-y-1 rounded-md bg-red-50 p-3 max-h-32 overflow-y-auto">
              <p className="text-sm font-medium text-red-800">Details:</p>
              <ul className="list-disc list-inside text-sm text-red-700">
                {uploadErrors.map((error, index) => (
                  <li key={index}>
                    <span className="font-semibold">{error.name}:</span>{" "}
                    {error.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Create Button */}
          <div className="pt-5 text-right">
            <button
              type="button"
              onClick={handleCreateClick}
              disabled={!title.trim() || isSubmitting}
              className={`inline-flex items-center justify-center rounded-lg px-6 py-2.5 text-sm font-medium text-white shadow-md transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white ${
                !title.trim() || isSubmitting
                  ? "cursor-not-allowed bg-purple-300"
                  : "bg-purple-600 hover:bg-purple-700"
              }`}
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                  Processing...
                </>
              ) : (
                "Create"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePageModal;
