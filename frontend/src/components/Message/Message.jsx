/**
 * Message Component
 * Displays a single chat message with markdown support
 */

import React from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { User, Bot, Loader2 } from "lucide-react";
import "./Message.css";

const Message = ({ message, isLoading = false }) => {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "user-message" : "assistant-message"}`}>
      <div className="message-icon">
        {isLoading ? (
          <Loader2 className="icon spinning" />
        ) : isUser ? (
          <User className="icon" />
        ) : (
          <Bot className="icon" />
        )}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">
            {isUser ? "You" : message.model || "Assistant"}
          </span>
          {message.timestamp && (
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        <div className="message-text">
          {isLoading ? (
            <div className="loading-dots">
              <span>Thinking</span>
              <span className="dot">.</span>
              <span className="dot">.</span>
              <span className="dot">.</span>
            </div>
          ) : (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;
