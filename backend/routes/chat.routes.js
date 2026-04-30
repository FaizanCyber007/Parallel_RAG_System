/**
 * Chat Routes
 * Handles all chat-related endpoints
 */

import express from "express";
import { llmServiceFactory } from "../services/llm/index.js";
import { getModelsList } from "../config/models.config.js";
import { chatHistoryService } from "../services/chatHistory.service.js";
import { metricsService } from "../services/metrics.service.js";

/* 🔥 OCR imports */
import multer from "multer";
import axios from "axios";
import FormData from "form-data";

const router = express.Router();

/* ===========================
   CHAT HISTORY ROUTES
=========================== */

router.get("/history", async (req, res) => {
  try {
    const sessions = await chatHistoryService.getSessions();
    res.json({ success: true, history: sessions });
  } catch (error) {
    res.status(500).json({ success: false, error: "Failed to fetch history" });
  }
});

router.get("/history/:id", async (req, res) => {
  try {
    const session = await chatHistoryService.getSession(req.params.id);
    if (!session)
      return res.status(404).json({ success: false, error: "Session not found" });
    res.json({ success: true, session });
  } catch (error) {
    res.status(500).json({ success: false, error: "Failed to fetch session" });
  }
});

router.post("/history", async (req, res) => {
  const session = await chatHistoryService.createSession();
  res.json({ success: true, session });
});

router.delete("/history", async (req, res) => {
  await chatHistoryService.clearHistory();
  res.json({ success: true });
});

router.delete("/history/:id", async (req, res) => {
  await chatHistoryService.deleteSession(req.params.id);
  res.json({ success: true });
});

/* ===========================
   NORMAL RAG CHAT (UNCHANGED)
=========================== */

router.post("/", async (req, res) => {
  const startTime = Date.now();
  try {
    const { modelId, message, conversationHistory = [], conversationId } =
      req.body;

    if (!modelId || !message?.trim()) {
      return res
        .status(400)
        .json({ success: false, error: "Model and message required" });
    }

    const userMessage = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };

    const result = await llmServiceFactory.generateResponse(
      modelId,
      message,
      conversationHistory
    );

    const latencyMs = Date.now() - startTime;

    if (!result.success) return res.status(500).json(result);

    let sessionId = conversationId;
    if (!sessionId) {
      const newSession = await chatHistoryService.createSession();
      sessionId = newSession.id;
    }

    const assistantMessage = {
      role: "assistant",
      content: result.response,
      model: result.model,
      modelId: result.modelId,
      timestamp: new Date().toISOString(),
      metrics: {
        latencyMs,
        inputTokens: result.usage?.prompt_tokens,
        outputTokens: result.usage?.completion_tokens,
      },
    };

    await chatHistoryService.saveMessage(
      sessionId,
      userMessage,
      assistantMessage
    );

    await metricsService.logMetrics({
      conversationId: sessionId,
      modelId,
      prompt: message,
      response: result.response,
      latencyMs,
      usage: result.usage,
    });

    res.json({
      ...result,
      conversationId: sessionId,
      metrics: assistantMessage.metrics,
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

/* ===========================
   OCR + FILE CHAT (NEW)
=========================== */

const upload = multer({ storage: multer.memoryStorage() });

router.post("/chat-with-files", upload.array("files"), async (req, res) => {
  try {
    const { message, modelId, conversationId } = req.body;
    const files = req.files;

    if (!files || files.length === 0) {
      return res.json({ extracted_text: "No files received." });
    }

    /* Send files to Python OCR */
    const formData = new FormData();
    files.forEach((file) =>
      formData.append("files", file.buffer, file.originalname)
    );

    const ocrResponse = await axios.post(
      "http://localhost:8000/extract-text",
      formData,
      { headers: formData.getHeaders() }
    );

    const extractedText =
      ocrResponse.data.extracted_text || "No text extracted.";

    let sessionId = conversationId;
    if (!sessionId) {
      const newSession = await chatHistoryService.createSession();
      sessionId = newSession.id;
    }

    const fileNames = files.map((f) => f.originalname).join(", ");
    const userMessage = {
      role: "user",
      content: `${message || ""}\n📎 Files: ${fileNames}`,
      timestamp: new Date().toISOString(),
    };

    let assistantMessage;
    let finalResponse;

    /* Extraction only */
    if (!message || message.toLowerCase().includes("extract")) {
      assistantMessage = {
        role: "assistant",
        content: extractedText,
        model: "ocr",
        modelId: "ocr",
        timestamp: new Date().toISOString(),
      };

      finalResponse = { extracted_text: extractedText };
    } else {
      /* RAG QUERY */
      const result = await llmServiceFactory.generateResponse(
        modelId || "deepseek-v3.2-exp",
        `${message}\n\n${extractedText}`
      );

      assistantMessage = {
        role: "assistant",
        content: result.response,
        model: result.model,
        modelId: result.modelId,
        timestamp: new Date().toISOString(),
      };

      finalResponse = {
        extracted_text: result.response,
        is_rag_response: true,
      };
    }

    await chatHistoryService.saveMessage(
      sessionId,
      userMessage,
      assistantMessage
    );

    res.json({ ...finalResponse, conversationId: sessionId });
  } catch (err) {
    res.status(500).json({ extracted_text: "OCR failed." });
  }
});

/* ===========================
   MODELS & HEALTH
=========================== */

router.get("/models", (req, res) => {
  const models = getModelsList();
  const services = llmServiceFactory.getAvailableServices();
  res.json({
    success: true,
    models: models.all.map((m) => ({
      ...m,
      available: services[m.provider] || false,
    })),
  });
});

router.get("/health", (req, res) => {
  const services = llmServiceFactory.getAvailableServices();
  res.json({ success: true, status: "online", services });
});

export default router;
