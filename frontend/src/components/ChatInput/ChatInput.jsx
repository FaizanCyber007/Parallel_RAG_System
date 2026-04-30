/**
 * ChatInput Component
 * RAG-safe text input + OCR file upload
 */

import React, { useState, useRef, useEffect } from "react";
import { Send, Plus, X } from "lucide-react";
import "./ChatInput.css";

const ChatInput = ({
  onSendMessage,
  disabled = false,
  selectedModel,
}) => {
  const [message, setMessage] = useState("");
  const [rerank, setRerank] = useState(true);
  const [files, setFiles] = useState([]);

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  /* ---------------- FILE HANDLING (OCR) ---------------- */

  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files);
    setFiles((prev) => [...prev, ...selected]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  /* ---------------- SEND HANDLING ---------------- */

  const handleSubmit = (e) => {
    e.preventDefault();

    if ((!message.trim() && files.length === 0) || disabled || !selectedModel)
      return;

    // 🔥 RAG-SAFE PAYLOAD
    onSendMessage({
      message,
      rerank,
      files, // backend supports OCR
    });

    setMessage("");
    setFiles([]);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  /* ---------------- AUTO-RESIZE TEXTAREA ---------------- */

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  /* ---------------- UI ---------------- */

  return (
    <div className="chat-input-container">
      {/* FILE PREVIEW */}
      {files.length > 0 && (
        <div className="file-preview">
          {files.map((file, i) => (
            <div key={i} className="file-chip">
              {file.type.startsWith("image") ? (
                <img
                  src={URL.createObjectURL(file)}
                  alt=""
                  className="file-thumb"
                />
              ) : (
                <span>📄 {file.name}</span>
              )}
              <X size={14} onClick={() => removeFile(i)} />
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        {/* FILE PICKER */}
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={disabled || !selectedModel}
          title="Upload file for OCR"
        >
          <Plus />
        </button>

        <input
          type="file"
          multiple
          hidden
          ref={fileInputRef}
          accept="image/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
        />

        {/* TEXT INPUT */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            selectedModel
              ? "Type your message… (Shift+Enter for new line)"
              : "Please select a model first…"
          }
          disabled={disabled || !selectedModel}
          className="chat-input-textarea"
          rows={1}
        />

        {/* SEND */}
        <button
          type="submit"
          disabled={
            disabled ||
            (!message.trim() && files.length === 0) ||
            !selectedModel
          }
          className="chat-input-button"
        >
          <Send className="icon" />
        </button>
      </form>

      {/* CONTROLS */}
      <div className="chat-input-controls">
        <label className="rerank-checkbox">
          <input
            type="checkbox"
            checked={rerank}
            onChange={(e) => setRerank(e.target.checked)}
          />
          <span>Rerank</span>
        </label>
      </div>

      {/* MODEL INFO */}
      {selectedModel && (
        <div className="chat-input-info">
          <span className="model-indicator">Using: {selectedModel}</span>
        </div>
      )}
    </div>
  );
};

export default ChatInput;
