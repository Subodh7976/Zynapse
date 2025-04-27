"use client";

import React, { useState } from 'react';
import WavyBackground from '@/components/WavyBackground';
import CreatePageModal from '@/components/CreatePageModal';

export default function HomePage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-white p-6 overflow-hidden">
      {/* Wavy Background Component */}
      <WavyBackground />

      {/* Main Content */}
      <div className="relative z-10 text-center">
        {/* Project Name */}
        <h1 className="mb-6 text-9xl font-semibold text-gray-900">
          Zynapse
        </h1>

        {/* Create Page Button - Add onClick */}
        <button
          type="button"
          onClick={openModal} // Open the modal on click
          className="rounded-lg bg-purple-600 px-8 py-3 text-lg font-medium text-white shadow-md transition-colors duration-200 ease-in-out hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white"
        >
          Create Page
        </button>
      </div>

      {/* Render the Modal */}
      <CreatePageModal
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </main>
  );
}