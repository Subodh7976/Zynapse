// src/app/page.tsx
import React from 'react';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white p-6">
      <div className="text-center">
        {/* Project Name */}
        <h1 className="mb-6 text-9xl font-semibold text-gray-900">
          Zynapse
        </h1>

        {/* Create Page Button */}
        <button
          type="button"
          // We will add onClick functionality later to open the modal
          className="rounded-lg bg-purple-600 px-8 py-3 text-lg font-medium text-white shadow-md transition-colors duration-200 ease-in-out hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white"
        >
          Create Page
        </button>
      </div>
    </main>
  );
}