'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/avatar';
import { Alert } from '@/components/ui/Alert';
import toast from 'react-hot-toast';

interface ProfileImageUploadProps {
  currentImage?: string;
  onImageChange: (file: File | null) => void;
  loading?: boolean;
  maxSize?: number; // in MB
  acceptedTypes?: string[];
  className?: string;
}

export function ProfileImageUpload({
  currentImage,
  onImageChange,
  loading = false,
  maxSize = 5,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  className = '',
}: ProfileImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    // Check file type
    if (!acceptedTypes.includes(file.type)) {
      toast.error(`Please select a valid image file (${acceptedTypes.map(type => type.split('/')[1]).join(', ')})`);
      return false;
    }

    // Check file size
    const maxSizeBytes = maxSize * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      toast.error(`Image size must be less than ${maxSize}MB`);
      return false;
    }

    return true;
  };

  const handleFileSelect = (file: File) => {
    if (!validateFile(file)) {
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Notify parent component
    onImageChange(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleRemoveImage = () => {
    setPreview(null);
    onImageChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };

  const displayImage = preview || currentImage;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Image Preview */}
      <div className="flex items-center space-x-6">
        <Avatar className="h-24 w-24">
          {displayImage ? (
            <img
              src={displayImage}
              alt="Profile preview"
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="h-full w-full bg-gray-300 flex items-center justify-center">
              <svg
                className="h-8 w-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
          )}
        </Avatar>

        <div className="flex-1">
          <div className="flex space-x-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleClickUpload}
              disabled={loading}
            >
              {displayImage ? 'Change Photo' : 'Upload Photo'}
            </Button>
            
            {displayImage && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleRemoveImage}
                disabled={loading}
                className="text-red-600 border-red-300 hover:bg-red-50"
              >
                Remove
              </Button>
            )}
          </div>
          
          <p className="mt-2 text-xs text-gray-500">
            {acceptedTypes.map(type => type.split('/')[1]).join(', ').toUpperCase()}. Max size {maxSize}MB.
          </p>
        </div>
      </div>

      {/* Drag and Drop Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="mt-4">
          <p className="text-sm text-gray-600">
            <button
              type="button"
              className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
              onClick={handleClickUpload}
            >
              Click to upload
            </button>{' '}
            or drag and drop
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {acceptedTypes.map(type => type.split('/')[1]).join(', ').toUpperCase()} up to {maxSize}MB
          </p>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleFileInputChange}
        className="sr-only"
      />

      {/* Loading State */}
      {loading && (
        <Alert variant="default">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Uploading image...</span>
          </div>
        </Alert>
      )}
    </div>
  );
}